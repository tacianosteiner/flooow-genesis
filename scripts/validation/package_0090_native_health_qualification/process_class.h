/* Finite disposable process contract. Classification never grants eligibility. */
#ifndef FLOOOW_PROCESS_CLASS_H
#define FLOOOW_PROCESS_CLASS_H
static inline int process_class(const char *kind,int roster){
    if(!strcmp(kind,"client backend"))return roster?1:2;
    if(!strcmp(kind,"parallel worker")||!strcmp(kind,"background worker"))return roster?3:2;
    const char *internal[]={"autovacuum worker","autovacuum launcher","checkpointer","background writer","walwriter","wal writer","walreceiver","wal receiver","walsender","wal sender","logical replication launcher","logical replication worker","startup","startup process","archiver","slotsync worker","slot sync worker","walsummarizer","wal summarizer","io worker"};
    for(unsigned i=0;i<sizeof(internal)/sizeof(internal[0]);i++)if(!strcmp(kind,internal[i]))return 2;
    return 0; /* Unknown process type: ambiguity, never silently excluded. */
}
#endif
