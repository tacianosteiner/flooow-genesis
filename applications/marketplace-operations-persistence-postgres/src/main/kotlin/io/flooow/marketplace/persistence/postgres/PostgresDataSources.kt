package io.flooow.marketplace.persistence.postgres

import javax.sql.DataSource
import org.postgresql.ds.PGSimpleDataSource

object PostgresDataSources {
    fun create(configuration: PostgresConfiguration): DataSource =
        PGSimpleDataSource().apply {
            setUrl(configuration.url)
            user = configuration.user
            password = configuration.password
        }
}
