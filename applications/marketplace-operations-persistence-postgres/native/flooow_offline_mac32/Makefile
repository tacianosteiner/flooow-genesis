EXTENSION = flooow_offline_mac32
MODULE_big = flooow_offline_mac32
OBJS = flooow_offline_mac32.o
DATA = flooow_offline_mac32--1.0.sql

PG_CONFIG ?= pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)

PG_CFLAGS += -fvisibility=hidden -fno-lto
PG_LDFLAGS += -fno-lto
SHLIB_LINK += -lcrypto

include $(PGXS)
