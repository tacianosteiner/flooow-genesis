package io.flooow.marketplace.operations.economics.provider.omie

import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceV3Capability
import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceV3Record
import kotlin.test.Test
import kotlin.test.assertEquals

class OmieProviderConnectorV3Test {
    @Test
    fun `default Omie provider registration exposes V3 exactly once with V3 record type`() {
        val connector = OmieProviderConnector()

        val definitions = connector.descriptor.definitions.filter {
            it.capability == OmieTransactionEvidenceV3Capability.KEY
        }

        assertEquals(1, definitions.size)
        assertEquals(
            OmieTransactionEvidenceV3Record::class,
            definitions.single().recordType
        )
    }
}
