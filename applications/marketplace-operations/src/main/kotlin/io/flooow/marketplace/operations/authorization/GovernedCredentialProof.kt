package io.flooow.marketplace.operations.authorization

/**
 * Package0090 protected proof derivation reuses the exact existing credential
 * digest without creating an additional immutable verifier buffer. The caller
 * owns this array and must erase it after S16 and before decision writer entry.
 * This pure bridge confers no authenticated actor or database authority.
 */
object GovernedCredentialProof {
    fun derive(credential: CommandCredential): ByteArray = credential.digest()
}
