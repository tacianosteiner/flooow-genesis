#include "postgres.h"

#include "access/detoast.h"
#include "fmgr.h"
#include "varatt.h"

#include <openssl/crypto.h>

PG_MODULE_MAGIC;

PG_FUNCTION_INFO_V1(timing_safe_equal32);

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
