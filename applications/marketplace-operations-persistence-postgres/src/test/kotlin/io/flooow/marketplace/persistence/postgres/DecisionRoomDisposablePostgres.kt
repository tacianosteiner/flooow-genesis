package io.flooow.marketplace.persistence.postgres

import com.github.dockerjava.api.model.ExposedPort
import com.github.dockerjava.api.model.PortBinding
import com.github.dockerjava.api.model.Ports
import org.testcontainers.postgresql.PostgreSQLContainer

/** Disposable product-schema fixture only; never PACKAGE-0090/V043 proof. */
internal fun decisionRoomDisposablePostgres(): PostgreSQLContainer =
    PostgreSQLContainer("postgres:18.4")
        .withLabel("flooow.authority", "mvp-autonomous-completion-v1")
        .withCreateContainerCmdModifier { command ->
            requireNotNull(command.hostConfig).withPortBindings(
                PortBinding(Ports.Binding.bindIpAndPort("127.0.0.1", 0), ExposedPort.tcp(5432))
            )
        }
