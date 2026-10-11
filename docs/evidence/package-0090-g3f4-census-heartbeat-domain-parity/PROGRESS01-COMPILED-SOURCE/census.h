/* Independent pg_stat_activity enumeration, never registry-derived discovery.
 * Numeric PID is corroboration only. Unknown processes select the retained
 * postmaster anchor for coarse fail-closed generation shutdown, never PID kill.
 */
static int independent_census(uint64_t until){
    PGconn *db=PQconnectStart("host=/tmp/pgsock dbname=native_fixture user=postgres");if(!db)return 0;
    for(;;){PostgresPollingStatusType s=PQconnectPoll(db);if(s==PGRES_POLLING_OK)break;
        if((s!=PGRES_POLLING_READING&&s!=PGRES_POLLING_WRITING)||!wait_fd(PQsocket(db),s==PGRES_POLLING_READING?POLLIN:POLLOUT,until)){PQfinish(db);return 0;}}
    if(PQsetnonblocking(db,1)){PQfinish(db);return 0;}
    char oids[4][24];const char *v[8];for(unsigned i=0;i<4;i++){snprintf(oids[i],sizeof(oids[i]),"%u",current.role_oid[i]);v[i]=oids[i];v[i+4]=current.role_name[i];}
    if(!PQsendQueryParams(db,"SELECT pid,usesysid,datid,(extract(epoch from backend_start)*1000000-946684800000000)::bigint,(extract(epoch from pg_postmaster_start_time())*1000000-946684800000000)::bigint,usename FROM pg_catalog.pg_stat_activity WHERE backend_type='client backend' AND (usesysid IN ($1::oid,$2::oid,$3::oid,$4::oid) OR usename IN ($5,$6,$7,$8))",8,NULL,v,NULL,NULL,0)){PQfinish(db);return 0;}
    for(;;){int f=PQflush(db);if(!f)break;if(f<0||!wait_fd(PQsocket(db),POLLOUT,until)){PQfinish(db);return 0;}}
    while(PQisBusy(db)){if(!wait_fd(PQsocket(db),POLLIN,until)||!PQconsumeInput(db)){PQfinish(db);return 0;}}
    unsigned char seen[128]={0};
    PGresult *r=PQgetResult(db);int ok=r&&PQresultStatus(r)==PGRES_TUPLES_OK;
    if(ok)for(int row=0;row<PQntuples(r);row++){
        int matches=0;const char *classification="BACKEND_NOT_REGISTERED";
        for(unsigned i=0;i<used;i++)if(registry[i].fd>=0&&alive(registry[i].fd)&&registry[i].pid==atoi(PQgetvalue(r,row,0))){
            matches++;seen[i]=1;request_fields *e=&registry[i].request;
            classification=(e->postmaster_start!=strtoll(PQgetvalue(r,row,4),NULL,10))?"GENERATION_MISMATCH":
                e->role!=strtoul(PQgetvalue(r,row,1),NULL,10)||e->db!=strtoul(PQgetvalue(r,row,2),NULL,10)||e->backend_start!=strtoll(PQgetvalue(r,row,3),NULL,10)||strcmp(e->role_name,PQgetvalue(r,row,5))?"IDENTITY_MISMATCH":"MATCHED";
        }
        if(matches>1)classification="AMBIGUOUS";
        printf("{\"event\":\"server_census\",\"classification\":\"%s\",\"pid\":%s,\"at_us\":%llu}\n",classification,PQgetvalue(r,row,0),(unsigned long long)tick_us());
        if(strcmp(classification,"MATCHED"))ok=0;
    }
    if(r&&PQresultStatus(r)==PGRES_TUPLES_OK)for(unsigned i=0;i<used;i++)if(registry[i].fd>=0&&alive(registry[i].fd)&&!seen[i]){
        printf("{\"event\":\"server_census\",\"classification\":\"REGISTRY_ENTRY_NO_BACKEND\",\"pid\":%d,\"at_us\":%llu}\n",registry[i].pid,(unsigned long long)tick_us());ok=0;
    }
    if(r)PQclear(r);PQfinish(db);return ok;
}
