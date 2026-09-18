package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.connector.*
import io.flooow.integration.control.*
import io.flooow.marketplace.operations.economics.provider.*
import io.flooow.organization.OrganizationId
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.sql.DriverManager
import java.time.Clock
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.util.UUID
import org.testcontainers.postgresql.PostgreSQLContainer
import kotlin.test.*

class PostgresOmieTransactionEvidenceV3CommitterTest {
    private val now = Instant.parse("2026-09-18T14:30:00Z")
    private val clock = Clock.fixed(now, ZoneOffset.UTC)
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration
    private lateinit var repository: PostgresIntegrationControlPlaneRepository
    private lateinit var service: IntegrationControlPlaneService
    private lateinit var vault: V3TestVault
    private lateinit var protector: V3TestProtector
    private var identifier = 1000L

    @BeforeTest
    fun startPostgres() {
        postgres = PostgreSQLContainer("postgres:18.4")
        postgres.start()

        configuration =
            PostgresConfiguration(
                postgres.jdbcUrl,
                postgres.username,
                postgres.password
            )

        repository =
            PostgresIntegrationControlPlaneRepository.connect(configuration)

        vault = V3TestVault()
        protector = V3TestProtector()

        service = IntegrationControlPlaneService(
            repository,
            vault,
            clock,
            organizationIds = IdentifierFactory {
                OrganizationId(UUID(0, identifier++))
            },
            connectionIds = IdentifierFactory {
                IntegrationConnectionId(UUID(1, identifier++))
            },
            auditIds = IdentifierFactory {
                IntegrationAuditEntryId(UUID(2, identifier++))
            },
            correlationIds = IdentifierFactory {
                UUID(3, identifier++)
            }
        )
    }

    @AfterTest
    fun stopPostgres() = postgres.stop()

    @Test
    fun `v3 page persists base sidecar lines and independent progress atomically`() {
        val active = activeConnection()
        val record = record()
        val connector = V3RecordConnector(record)

        val runtime = ConnectorRuntime(
            IntegrationControlPlaneConnectorAccess(service),
            listOf(connector),
            listOf(
                PostgresOmieTransactionEvidenceV3Committer(
                    configuration,
                    protector,
                    clock
                )
            ),
            clock
        )

        val first = assertIs<ConnectorExecutionOutcome.Success>(
            runtime.execute(invocation(active))
        )

        assertEquals(ConnectorSuccessKind.COMMITTED, first.kind)
        assertEquals(1, count("integration_omie_transaction_evidence"))
        assertEquals(1, count("integration_omie_transaction_evidence_v3"))
        assertEquals(2, count("integration_omie_transaction_evidence_v3_line"))
        assertEquals(1, count("integration_connector_page_commit"))

        val semantic = stringValue(
            "SELECT source_evidence_semantic_fingerprint " +
                "FROM integration_omie_transaction_evidence_v3"
        )
        assertEquals(record.sourceEvidenceSemanticFingerprint, semantic)

        val replay = assertIs<ConnectorExecutionOutcome.Success>(
            runtime.execute(invocation(active))
        )
        assertEquals(ConnectorSuccessKind.ALREADY_COMMITTED, replay.kind)
        assertEquals(1, connector.invocations)
        assertEquals(1, count("integration_omie_transaction_evidence"))
    }

    @Test
    fun `v3 base sidecar and lines are immutable`() {
        val active = activeConnection()
        val record = record()

        assertIs<ConnectorExecutionOutcome.Success>(
            runtime(active, V3RecordConnector(record))
                .execute(invocation(active))
        )

        assertFails {
            execute(
                "UPDATE integration_omie_transaction_evidence_v3 " +
                    "SET source_cancelled=true"
            )
        }

        assertFails {
            execute(
                "UPDATE integration_omie_transaction_evidence_v3_line " +
                    "SET quantity=999"
            )
        }

        assertFails {
            execute(
                "UPDATE integration_omie_transaction_evidence " +
                    "SET source_status='X' " +
                    "WHERE capability='" +
                    OmieTransactionEvidenceV3Capability.VALUE +
                    "'"
            )
        }

        assertFails {
            execute(
                "DELETE FROM integration_omie_transaction_evidence " +
                    "WHERE capability='" +
                    OmieTransactionEvidenceV3Capability.VALUE +
                    "'"
            )
        }
    }

    @Test
    fun `v3 persistence failure rolls back base sidecar lines page and progress`() {
        val active = activeConnection()

        execute(
            """
            CREATE FUNCTION reject_v3_sidecar_test()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION 'injected-v3-sidecar-failure';
            END
            $$;

            CREATE TRIGGER reject_v3_sidecar_test
            BEFORE INSERT ON integration_omie_transaction_evidence_v3
            FOR EACH ROW
            EXECUTE FUNCTION reject_v3_sidecar_test();
            """.trimIndent()
        )

        val outcome =
            runtime(active, V3RecordConnector(record()))
                .execute(invocation(active))

        assertIs<ConnectorExecutionOutcome.Failure>(outcome)

        assertEquals(0, count("integration_omie_transaction_evidence"))
        assertEquals(0, count("integration_omie_transaction_evidence_v3"))
        assertEquals(0, count("integration_omie_transaction_evidence_v3_line"))
        assertEquals(0, count("integration_connector_page_commit"))
        assertEquals(0, count("integration_connector_progress"))
    }

    private fun runtime(
        active: Pair<OrganizationId, IntegrationConnectionId>,
        connector: V3RecordConnector
    ) = ConnectorRuntime(
        IntegrationControlPlaneConnectorAccess(service),
        listOf(connector),
        listOf(
            PostgresOmieTransactionEvidenceV3Committer(
                configuration,
                protector,
                clock
            )
        ),
        clock
    )

    private fun activeConnection():
        Pair<OrganizationId, IntegrationConnectionId> {
        val organization = service.createOrganization()
        val connection = service.createConnection(
            organization.id,
            ProviderKey.of("omie"),
            CredentialKind.STATIC_API_CREDENTIAL
        )

        service.bindInitialCredential(
            organization.id,
            connection.id,
            """{"schemaVersion":1,"appKey":"test","appSecret":"test"}"""
                .toByteArray()
        )

        return organization.id to connection.id
    }

    private fun invocation(
        active: Pair<OrganizationId, IntegrationConnectionId>
    ) = ConnectorInvocation(
        active.first,
        active.second,
        OmieTransactionEvidenceV3Capability.KEY,
        ConnectorInvocationId(UUID.randomUUID()),
        ConnectorBudget(now.plusSeconds(30), 100, 100_000)
    )

    private fun record(): OmieTransactionEvidenceV3Record {
        val line1 = OmieTransactionEvidenceV3Line(
            internalItemReference = OmieOrderItemReference.of("10"),
            integrationItemReference =
                OmieOrderItemIntegrationReference.of("ITEM-10"),
            productIdentifiers = listOf(
                OmieTransactionProductIdentifier.of(
                    OmieTransactionProductIdentifierKind.INTERNAL_PRODUCT_ID,
                    "101"
                ),
                OmieTransactionProductIdentifier.of(
                    OmieTransactionProductIdentifierKind.INTEGRATION_PRODUCT_CODE,
                    "PROD-101"
                )
            ),
            quantity = ProviderSourceDecimal.parse("1"),
            unitValue = ProviderSourceDecimal.parse("60"),
            discountType = OmieDiscountType.of("V"),
            discountPercent = ProviderSourceDecimal.parse("0"),
            discountValue = ProviderSourceDecimal.parse("5"),
            deductionValue = ProviderSourceDecimal.parse("0"),
            merchandiseValue = ProviderSourceDecimal.parse("60"),
            totalValue = ProviderSourceDecimal.parse("55"),
            doNotGenerateFinancial = true,
            doNotSumTotal = false,
            kit = false,
            kitComponent = false,
            kitParentItemReference = null
        )

        val line2 = OmieTransactionEvidenceV3Line(
            internalItemReference = OmieOrderItemReference.of("11"),
            integrationItemReference =
                OmieOrderItemIntegrationReference.of("ITEM-11"),
            productIdentifiers = listOf(
                OmieTransactionProductIdentifier.of(
                    OmieTransactionProductIdentifierKind.INTERNAL_PRODUCT_ID,
                    "102"
                )
            ),
            quantity = ProviderSourceDecimal.parse("1"),
            unitValue = ProviderSourceDecimal.parse("50"),
            discountType = OmieDiscountType.of("V"),
            discountPercent = ProviderSourceDecimal.parse("0"),
            discountValue = ProviderSourceDecimal.parse("5"),
            deductionValue = ProviderSourceDecimal.parse("0"),
            merchandiseValue = ProviderSourceDecimal.parse("50"),
            totalValue = ProviderSourceDecimal.parse("45"),
            doNotGenerateFinancial = false,
            doNotSumTotal = false,
            kit = false,
            kitComponent = false,
            kitParentItemReference = null
        )

        return OmieTransactionEvidenceV3Record(
            orderReference = OmieOrderReference.of("123"),
            integrationOrderReference = OmieIntegrationReference.of("ERP-1"),
            customerOrderReference =
                OmieCustomerOrderReference.of("ML-123"),
            sourceOrderOrigin = OmieOrderOrigin.of("MLV"),
            status = OmieOrderStatus.of("60"),
            currency = null,
            providerCreatedLocal =
                LocalDateTime.parse("2026-09-10T08:15:30"),
            providerModifiedLocal =
                LocalDateTime.parse("2026-09-11T09:16:31"),
            cancelled = false,
            cancelledLocal = null,
            invoiced = true,
            invoicedLocal =
                LocalDateTime.parse("2026-09-11T10:00:00"),
            authorized = true,
            denied = false,
            returned = false,
            partiallyReturned = false,
            orderEnded = false,
            orderEndedReason = null,
            orderEndedLocal = null,
            orderDiscountType = OmieDiscountType.of("V"),
            orderDiscountPercent = ProviderSourceDecimal.parse("0"),
            orderDiscountAmount = ProviderSourceDecimal.parse("0"),
            totalOrderAmount = ProviderSourceDecimal.parse("100"),
            merchandiseAmount = ProviderSourceDecimal.parse("110"),
            discountAmount = ProviderSourceDecimal.parse("10"),
            deductionAmount = ProviderSourceDecimal.parse("0"),
            freightAmount = ProviderSourceDecimal.parse("2"),
            insuranceAmount = ProviderSourceDecimal.parse("1"),
            otherExpenseAmount = ProviderSourceDecimal.parse("0.5"),
            marketplaceFeeAmount = ProviderSourceDecimal.parse("3"),
            marketplaceShippingAmount = ProviderSourceDecimal.parse("4"),
            additionalOrderTotals = mapOf(
                "valor_icms" to ProviderSourceDecimal.parse("18")
            ),
            lines = listOf(line1, line2),
            observedAt = now,
            sourceFingerprint =
                "1".repeat(64),
            sourceEvidenceSemanticFingerprint =
                "2".repeat(64)
        )
    }

    private fun count(table: String): Int {
        require(
            table in setOf(
                "integration_omie_transaction_evidence",
                "integration_omie_transaction_evidence_v3",
                "integration_omie_transaction_evidence_v3_line",
                "integration_connector_page_commit",
                "integration_connector_progress"
            )
        )

        return connection().use { c ->
            c.createStatement().use { s ->
                s.executeQuery("SELECT count(*) FROM $table").use { rs ->
                    rs.next()
                    rs.getInt(1)
                }
            }
        }
    }

    private fun stringValue(sql: String): String =
        connection().use { c ->
            c.createStatement().use { s ->
                s.executeQuery(sql).use { rs ->
                    rs.next()
                    rs.getString(1)
                }
            }
        }

    private fun execute(sql: String) =
        connection().use { c ->
            c.createStatement().use { it.execute(sql) }
        }

    private fun connection() =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        )
}

private class V3RecordConnector(
    private val record: OmieTransactionEvidenceV3Record
) : PullConnector {
    var invocations: Int = 0
        private set

    override val descriptor = ConnectorDescriptor(
        ProviderKey.of("omie"),
        listOf(
            ConnectorRecordDefinition(
                OmieTransactionEvidenceV3Capability.KEY,
                OmieTransactionEvidenceV3Record::class
            )
        )
    )

    override fun readPage(
        capability: ConnectorCapability,
        credentialBytes: ByteArray,
        currentProgress: ConnectorProgress?,
        budget: ConnectorBudget,
        cancellation: ConnectorCancellation
    ): ConnectorReadResult {
        invocations += 1
        return ConnectorReadResult.Page(
            ConnectorPage(
                listOf(record),
                null,
                record.observedAt,
                exhausted = true,
                responseBytes = 100
            )
        )
    }
}

private class V3TestVault : SecretVault {
    private val stored = mutableMapOf<SecretReference, ByteArray>()
    private var sequence = 0

    override fun store(
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        credentialBytes: ByteArray
    ): SecretReference = try {
        SecretReference.of("v3-test-vault://${++sequence}").also {
            stored[it] = credentialBytes.copyOf()
        }
    } finally {
        credentialBytes.fill(0)
    }

    override fun <T> withSecret(
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        reference: SecretReference,
        operation: (ByteArray) -> T
    ): T {
        val scoped = requireNotNull(stored[reference]).copyOf()
        return try {
            operation(scoped)
        } finally {
            scoped.fill(0)
        }
    }

    override fun revoke(
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        reference: SecretReference
    ) {
        stored.remove(reference)?.fill(0)
    }
}

private class V3TestProtector : ConnectorProgressProtector {
    override fun seal(
        context: ConnectorProgressProtectionContext,
        plaintextBytes: ByteArray
    ): SealedConnectorProgress {
        val contextBytes = contextBytes(context)
        val pad = MessageDigest.getInstance("SHA-256").digest(contextBytes)

        val ciphertext = ByteArray(plaintextBytes.size) { index ->
            (
                plaintextBytes[index].toInt() xor
                    pad[index % pad.size].toInt()
                ).toByte()
        }

        val tag =
            MessageDigest.getInstance("SHA-256")
                .digest(contextBytes + plaintextBytes)

        contextBytes.fill(0)
        pad.fill(0)

        val envelope = tag + ciphertext

        tag.fill(0)
        ciphertext.fill(0)

        return SealedConnectorProgress.take(envelope)
    }

    override fun open(
        context: ConnectorProgressProtectionContext,
        sealedProgress: SealedConnectorProgress
    ): ByteArray =
        sealedProgress.useBytes { envelope ->
            require(envelope.size >= 33)

            val contextBytes = contextBytes(context)
            val pad =
                MessageDigest.getInstance("SHA-256").digest(contextBytes)

            val ciphertext = envelope.copyOfRange(32, envelope.size)

            val plaintext = ByteArray(ciphertext.size) { index ->
                (
                    ciphertext[index].toInt() xor
                        pad[index % pad.size].toInt()
                    ).toByte()
            }

            val expected =
                MessageDigest.getInstance("SHA-256")
                    .digest(contextBytes + plaintext)

            val actual = envelope.copyOfRange(0, 32)

            contextBytes.fill(0)
            pad.fill(0)
            ciphertext.fill(0)

            val valid = MessageDigest.isEqual(expected, actual)

            expected.fill(0)
            actual.fill(0)

            if (!valid) {
                plaintext.fill(0)
                error("Protected progress unavailable")
            }

            plaintext
        }

    private fun contextBytes(
        context: ConnectorProgressProtectionContext
    ): ByteArray =
        listOf(
            context.organizationId.toString(),
            context.connectionId.value.toString(),
            context.capability.value,
            context.progressVersion.toString()
        ).joinToString("\n").toByteArray(StandardCharsets.UTF_8)
}
