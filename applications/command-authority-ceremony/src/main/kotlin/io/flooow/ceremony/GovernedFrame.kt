package io.flooow.ceremony

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.text.Normalizer
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.util.UUID

internal data class GovernedField(val name: String, val type: String)

/** SPEC 21.2 binary transport. Errors never render a value or a proof buffer. */
internal object GovernedFrame {
    const val ROOT = "FLOOOW/OFFLINE-FIELD-PROOF/"
    fun fields(declaration: String) = declaration.split(',').map {
        val parts = it.trim().split(' ', limit = 2)
        GovernedField(parts[0], parts[1].removePrefix("pg_catalog."))
    }
    fun encode(domain: String, fields: List<GovernedField>, values: Map<String, Any?>, nullable: Set<String> = emptySet()): ByteArray {
        require(values.keys == fields.map { it.name }.toSet()) { "TRANSPORT_FIELDS" }
        val bytes = ByteArrayOutputStream()
        DataOutputStream(bytes).use { out ->
            val name = text(domain)
            out.writeInt(name.size); out.write(name); out.writeShort(fields.size)
            fields.forEachIndexed { index, field ->
                val value = values[field.name]
                require(value != null || field.name in nullable) { "TRANSPORT_NULL" }
                val payload = if (value == null) byteArrayOf(0) else byteArrayOf(1) + scalar(field.type, value)
                out.writeShort(index + 1); out.writeInt(payload.size); out.write(payload)
            }
        }
        return bytes.toByteArray()
    }
    fun decode(domain: String, fields: List<GovernedField>, bytes: ByteArray, nullable: Set<String> = emptySet()): Map<String, Any?> {
        require(bytes.size <= 65536) { "TRANSPORT_BOUND" }
        val buffer = ByteBuffer.wrap(bytes)
        fun take(): ByteArray {
            require(buffer.remaining() >= 4) { "TRANSPORT_LENGTH" }
            val length = buffer.int
            require(length >= 0 && length <= buffer.remaining()) { "TRANSPORT_LENGTH" }
            return ByteArray(length).also(buffer::get)
        }
        require(take().contentEquals(text(domain))) { "TRANSPORT_DOMAIN" }
        require(buffer.remaining() >= 2 && buffer.short.toInt() == fields.size) { "TRANSPORT_COUNT" }
        val result = linkedMapOf<String, Any?>()
        fields.forEachIndexed { index, field ->
            require(buffer.remaining() >= 2 && buffer.short.toInt() == index + 1) { "TRANSPORT_TAG" }
            val payload = take()
            require(payload.isNotEmpty()) { "TRANSPORT_PRESENCE" }
            result[field.name] = when (payload[0].toInt()) {
                0 -> { require(payload.size == 1 && field.name in nullable) { "TRANSPORT_NULL" }; null }
                1 -> unscalar(field.type, payload.copyOfRange(1, payload.size))
                else -> error("TRANSPORT_PRESENCE")
            }
        }
        require(!buffer.hasRemaining()) { "TRANSPORT_TRAILING" }
        return result
    }
    private fun text(value: String): ByteArray {
        require(Normalizer.isNormalized(value, Normalizer.Form.NFC)) { "TRANSPORT_NFC" }
        val encoder = Charsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
        val encoded = encoder.encode(java.nio.CharBuffer.wrap(value))
        return ByteArray(encoded.remaining()).also(encoded::get)
    }
    private fun scalar(type: String, value: Any): ByteArray = when (type) {
        "uuid" -> (value as UUID).let { require(it != UUID(0, 0)); ByteBuffer.allocate(16).putLong(it.mostSignificantBits).putLong(it.leastSignificantBits).array() }
        "int4" -> ByteBuffer.allocate(4).putInt(value as Int).array()
        "int8" -> ByteBuffer.allocate(8).putLong(value as Long).array()
        "u32" -> (value as Long).let { require(it in 1..4294967295L); ByteBuffer.allocate(4).putInt(it.toInt()).array() }
        "bool" -> byteArrayOf(if (value as Boolean) 1 else 0)
        "bytea" -> (value as ByteArray).copyOf()
        "timestamptz" -> (value as Instant).let { require(it.nano % 1000 == 0); ByteBuffer.allocate(8).putLong(Math.addExact(Math.multiplyExact(it.epochSecond, 1000000), (it.nano / 1000).toLong())).array() }
        "timestamp without time zone" -> scalar("timestamptz", (value as LocalDateTime).toInstant(ZoneOffset.UTC))
        else -> { require(type == "text" || type.startsWith("char(")); text(value as String).also { if (type.startsWith("char(")) require(it.size == type.substringAfter('(').substringBefore(')').toInt() && it.all { b -> b.toInt() in 0..127 }) } }
    }
    private fun unscalar(type: String, bytes: ByteArray): Any {
        val buffer = ByteBuffer.wrap(bytes)
        return when (type) {
            "uuid" -> { require(bytes.size == 16); UUID(buffer.long, buffer.long).also { require(it != UUID(0, 0)) } }
            "int4" -> { require(bytes.size == 4); buffer.int }
            "int8" -> { require(bytes.size == 8); buffer.long }
            "u32" -> { require(bytes.size == 4); Integer.toUnsignedLong(buffer.int).also { require(it > 0) } }
            "bool" -> { require(bytes.size == 1 && bytes[0].toInt() in 0..1); bytes[0].toInt() == 1 }
            "bytea" -> bytes.copyOf()
            "timestamptz", "timestamp without time zone" -> {
                require(bytes.size == 8)
                val micros = buffer.long
                val instant = Instant.ofEpochSecond(Math.floorDiv(micros, 1000000), Math.floorMod(micros, 1000000).toLong() * 1000)
                if (type == "timestamptz") instant else LocalDateTime.ofInstant(instant, ZoneOffset.UTC)
            }
            else -> {
                val value = Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(buffer).toString()
                require(scalar(type, value).contentEquals(bytes)); value
            }
        }
    }
}
