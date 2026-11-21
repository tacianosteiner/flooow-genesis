#ifndef FLOOOW_PRIVATE_TEST_CREDENTIAL
#define FLOOOW_PRIVATE_TEST_CREDENTIAL
#include <libpq-fe.h>
#include <sys/types.h>
/* Existing HOST provisioning/Reader seam, no new credential authority. The
 * experiment does not establish credential-policy expiry/acceptance. */
typedef struct {int channel,birth;pid_t issuer;} S03PendingCredential;
S03PendingCredential s03_prepare_private_test_credential(void);
PGconn *s03_connect_private_test_reader(S03PendingCredential *pending);
#endif
