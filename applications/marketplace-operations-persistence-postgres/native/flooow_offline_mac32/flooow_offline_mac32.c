#include "postgres.h"

#include "access/detoast.h"
#include "fmgr.h"
#include "varatt.h"

#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/x509.h>

PG_MODULE_MAGIC;

PG_FUNCTION_INFO_V1(timing_safe_equal32);
/* Candidate only: no extension SQL binding until the error-contract hold in
 * PACKAGE-0090-ED25519-NATIVE-REVIEW.md is closed. Do not deploy this binary. */
PG_FUNCTION_INFO_V1(canonical_spki_ed25519_verify);

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
    key = d2i_PUBKEY(NULL, &cursor, 44);
    if (key == NULL || cursor != (const unsigned char *) VARDATA_ANY(spki) + 44 ||
        EVP_PKEY_id(key) != EVP_PKEY_ED25519 || i2d_PUBKEY(key, NULL) != 44)
    {
        EVP_PKEY_free(key);
        ereport(ERROR, (errcode(ERRCODE_INVALID_PARAMETER_VALUE),
                        errmsg("Invalid canonical Ed25519 SubjectPublicKeyInfo")));
    }
    result = i2d_PUBKEY(key, &output);
    if (result != 44 || memcmp(canonical, VARDATA_ANY(spki), 44) != 0)
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
    result = EVP_DigestVerify(context,
                             (const unsigned char *) VARDATA_ANY(signature), 64,
                             (const unsigned char *) VARDATA_ANY(message),
                             VARSIZE_ANY_EXHDR(message));
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
