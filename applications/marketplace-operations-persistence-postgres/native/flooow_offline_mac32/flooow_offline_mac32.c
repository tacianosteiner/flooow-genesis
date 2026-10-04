#include "postgres.h"

#include "access/detoast.h"
#include "fmgr.h"
#include "varatt.h"

#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/x509.h>

PG_MODULE_MAGIC;

PG_FUNCTION_INFO_V1(timing_safe_equal32);
/* Acceptance contract: only true accepts. Invalid encoded-point rejection is
 * false; structural input and operational failures remain distinct errors. */
PG_FUNCTION_INFO_V1(canonical_spki_ed25519_verify);

/* OpenSSL may append a decoder/provider error after an allocation error.
 * Inspect the whole operation's queue, never only the last error. */
static bool
openssl_operational_failure(void)
{
    unsigned long error;
    bool failed = false;

    while ((error = ERR_get_error()) != 0)
    {
        int reason = ERR_GET_REASON(error);

        if (reason == ERR_R_MALLOC_FAILURE || reason == ERR_R_INTERNAL_ERROR ||
            reason == ERR_R_SHOULD_NOT_HAVE_BEEN_CALLED)
            failed = true;
    }
    return failed;
}

Datum
canonical_spki_ed25519_verify(PG_FUNCTION_ARGS)
{
    bytea *spki;
    bytea *message;
    bytea *signature;
    const unsigned char *cursor;
    unsigned char canonical[44];
    unsigned char *output = canonical;
    EVP_PKEY *key = NULL;
    EVP_MD_CTX *context = NULL;
    int result;

    /* Frozen SignerPublicKeyInfo permits exactly 44-byte canonical SPKI. */
    if (toast_raw_datum_size(PG_GETARG_DATUM(0)) != VARHDRSZ + 44 ||
        toast_raw_datum_size(PG_GETARG_DATUM(2)) != VARHDRSZ + 64)
        ereport(ERROR, (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                        errmsg("Invalid Ed25519 structural input")));
    spki = PG_GETARG_BYTEA_PP(0);
    signature = PG_GETARG_BYTEA_PP(2);
    message = PG_GETARG_BYTEA_PP(1);
    cursor = (const unsigned char *) VARDATA_ANY(spki);
    ERR_clear_error();
    key = d2i_PUBKEY(NULL, &cursor, 44);
    if (key == NULL && openssl_operational_failure())
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 public key allocation failed")));
    if (key == NULL || cursor != (const unsigned char *) VARDATA_ANY(spki) + 44 ||
        EVP_PKEY_id(key) != EVP_PKEY_ED25519)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                        errmsg("Invalid canonical Ed25519 SubjectPublicKeyInfo")));
    }
    result = i2d_PUBKEY(key, NULL);
    if (result <= 0)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 public key encoding failed")));
    }
    if (result != 44)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                        errmsg("Invalid canonical Ed25519 SubjectPublicKeyInfo")));
    }
    result = i2d_PUBKEY(key, &output);
    if (result <= 0)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 public key encoding failed")));
    }
    if (result != 44)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 public key encoding invariant failed")));
    }
    if (memcmp(canonical, VARDATA_ANY(spki), 44) != 0)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                        errmsg("Invalid canonical Ed25519 SubjectPublicKeyInfo")));
    }
    context = EVP_MD_CTX_new();
    if (context == NULL || EVP_DigestVerifyInit(context, NULL, NULL, NULL, key) != 1)
    {
        EVP_MD_CTX_free(context);
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 verification initialization failed")));
    }
    ERR_clear_error();
    result = EVP_DigestVerify(context,
                             (const unsigned char *) VARDATA_ANY(signature), 64,
                             (const unsigned char *) VARDATA_ANY(message),
                             VARSIZE_ANY_EXHDR(message));
    if (openssl_operational_failure())
    {
        EVP_MD_CTX_free(context);
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 verification allocation failed")));
    }
    EVP_MD_CTX_free(context);
    EVP_PKEY_free(key);
    PG_FREE_IF_COPY(spki, 0);
    PG_FREE_IF_COPY(message, 1);
    PG_FREE_IF_COPY(signature, 2);
    if (result != 0 && result != 1)
        ereport(ERROR, (errcode(ERRCODE_INTERNAL_ERROR),
                        errmsg("Ed25519 verification failed operationally")));
    PG_RETURN_BOOL(result == 1);
}

Datum
timing_safe_equal32(PG_FUNCTION_ARGS)
{
    bytea *left;
    bytea *right;
    int comparison;

    /* SQL STRICT excludes NULL; reject oversized values before detoasting. */
    if (toast_raw_datum_size(PG_GETARG_DATUM(0)) != VARHDRSZ + 32 ||
        toast_raw_datum_size(PG_GETARG_DATUM(1)) != VARHDRSZ + 32)
        ereport(ERROR,
                (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                 errmsg("Invalid MAC length")));

    left = PG_GETARG_BYTEA_PP(0);
    right = PG_GETARG_BYTEA_PP(1);

    if (VARSIZE_ANY_EXHDR(left) != 32 ||
        VARSIZE_ANY_EXHDR(right) != 32)
        ereport(ERROR,
                (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                 errmsg("Invalid MAC length")));

    comparison = CRYPTO_memcmp(VARDATA_ANY(left), VARDATA_ANY(right), 32);

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(comparison == 0);
}
