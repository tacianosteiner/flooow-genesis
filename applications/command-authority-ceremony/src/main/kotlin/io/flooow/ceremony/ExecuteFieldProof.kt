package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.TransactionIdentityCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityWriteResult
import io.flooow.organization.OrganizationId
import java.security.SecureRandom
import java.time.Clock
import java.time.Instant
import java.util.Base64
import java.util.UUID

data class HumanApproval(val accountableOperator:String,val approvalSource:String,val windowStart:Instant,val windowEnd:Instant,val revocationOwner:String,val credentialCustodian:String,val credentialDeliveryMethod:String,val credentialRotationOwner:String,val immediateRevocationPolicy:String) {
 fun valid(now:Instant)=listOf(accountableOperator,approvalSource,revocationOwner,credentialCustodian,credentialDeliveryMethod,credentialRotationOwner,immediateRevocationPolicy).all(String::isNotBlank)&&!windowEnd.isBefore(windowStart)&&now in windowStart..windowEnd
}
data class FieldProofTarget(val organizationId:OrganizationId,val mercadoLivreConnectionId:UUID,val omieConnectionId:UUID,val sourceOrderReference:String,val integrationReference:String,val marketplaceOrderId:UUID,val reason:String,val provenance:String,val correlationId:UUID,val permission:CommandPermission=CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE) { fun valid()=sourceOrderReference.isNotBlank()&&integrationReference.isNotBlank()&&reason.isNotBlank()&&provenance.isNotBlank()&&permission==CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE }
interface ProtectedTty { fun isProtected():Boolean; fun deliverOnce(token:CharArray) }
interface RuntimeBoundary { fun matchesTarget(target:FieldProofTarget):Boolean; fun authenticate(token:String):AuthenticatedCommand?; fun write(actor:AuthenticatedCommand,command:TransactionIdentityCommand):TransactionIdentityWriteResult }
/** Test-only lifecycle signal. It deliberately exposes neither token nor credential bytes. */
internal interface CredentialLifecycleObserver { fun created(); fun destroyed(verifierCreationRejected:Boolean) }
sealed interface CeremonyResult { data class Applied(val principalId:UUID,val decisionId:UUID):CeremonyResult; data object Denied:CeremonyResult; data object IncompleteAuthority:CeremonyResult; data object WriterFailed:CeremonyResult }
/** Offline, single-process orchestration. No provider, HTTP, scheduler, or background work. */
class ExecuteFieldProof private constructor(private val issuer:ControlledCommandAuthorityIssuer,private val runtime:RuntimeBoundary,private val tty:ProtectedTty,private val clock:Clock,private val random:SecureRandom,private val credentialLifecycleObserver:CredentialLifecycleObserver?,@Suppress("UNUSED_PARAMETER") internalSeam:Unit) {
 constructor(issuer:ControlledCommandAuthorityIssuer,runtime:RuntimeBoundary,tty:ProtectedTty,clock:Clock,random:SecureRandom=SecureRandom()):this(issuer,runtime,tty,clock,random,null,Unit)
 internal constructor(issuer:ControlledCommandAuthorityIssuer,runtime:RuntimeBoundary,tty:ProtectedTty,clock:Clock,random:SecureRandom,credentialLifecycleObserver:CredentialLifecycleObserver):this(issuer,runtime,tty,clock,random,credentialLifecycleObserver,Unit)
 fun execute(approval:HumanApproval,target:FieldProofTarget,command:TransactionIdentityCommand):CeremonyResult {
  if(!approval.valid(clock.instant())||!target.valid()||!tty.isProtected()||command.marketplaceOrderId!=target.marketplaceOrderId||command.sourceOrderReference!=target.sourceOrderReference||command.correlationId!=target.correlationId||!runtime.matchesTarget(target))return CeremonyResult.Denied
  val principal=CommandPrincipalId(UUID.randomUUID());val id=UUID.randomUUID();val grant=UUID.randomUUID();val raw=ByteArray(32).also(random::nextBytes);val token="fc1.$id.${Base64.getUrlEncoder().withoutPadding().encodeToString(raw)}";raw.fill(0);val credential=CommandCredential.parse(token)?:return CeremonyResult.Denied;credentialLifecycleObserver?.created()
  var destroyed=false
  fun destroyCredential() {
   if(!destroyed) {
    credential.destroy()
    destroyed=true
    credentialLifecycleObserver?.destroyed(runCatching { CommandCredentialVerifier.fromCredential(credential) }.isFailure)
   }
  }
  try {
   if(!ok(issuer.issuePrincipal(PrincipalIssuance(UUID.randomUUID(),target.organizationId,principal,target.mercadoLivreConnectionId,target.omieConnectionId,target.reason,target.provenance,target.correlationId))))return CeremonyResult.IncompleteAuthority
   if(!ok(issuer.bindInitialCredential(InitialCredentialBinding(UUID.randomUUID(),target.organizationId,principal,credential,target.reason,target.provenance,target.correlationId))))return CeremonyResult.IncompleteAuthority
   tty.deliverOnce(token.toCharArray())
   if(!ok(issuer.grantPermission(PermissionGrant(UUID.randomUUID(),target.organizationId,principal,grant,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,target.reason,target.provenance,target.correlationId))))return CeremonyResult.IncompleteAuthority
   val actor=runtime.authenticate(token)?:return CeremonyResult.IncompleteAuthority
   destroyCredential()
   return when(runtime.write(actor,command)){is TransactionIdentityWriteResult.Applied,is TransactionIdentityWriteResult.AlreadyApplied->CeremonyResult.Applied(principal.value,command.decisionId);else->CeremonyResult.WriterFailed}
  } finally { destroyCredential() }
 }
 private fun ok(r:ControlledAuthorityResult)=r is ControlledAuthorityResult.Applied||r is ControlledAuthorityResult.AlreadyApplied
}
