#!/usr/bin/env bash
# Creates AWA Kafka topics with the partitioning strategy from the architecture
# document (Section 4.1 / 10): partition count sized for peak concurrent
# auctions, not concurrent users. Idempotent - safe to re-run.
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
# Local dev runs a single broker (replication factor 1). Production MUST set
# REPLICATION_FACTOR=3 (see architecture doc Section 11 - Kafka replication
# factor 3 is part of the HA design), e.g.:
#   REPLICATION_FACTOR=3 KAFKA_BOOTSTRAP_SERVERS=prod-kafka:9092 ./create_topics.sh
REPLICATION="${REPLICATION_FACTOR:-1}"

create_topic() {
  local name="$1" partitions="$2" replication="$3" retention_ms="$4"
  echo "Creating topic: ${name} (partitions=${partitions}, replication=${replication})"
  kafka-topics --bootstrap-server "${BOOTSTRAP}" \
    --create --if-not-exists \
    --topic "${name}" \
    --partitions "${partitions}" \
    --replication-factor "${replication}" \
    --config "retention.ms=${retention_ms}" \
    --config "min.insync.replicas=1"
}

# Bid events - partitioned by auction_id (set as the message key at publish
# time), NOT by any other field, so ordering per auction is guaranteed.
# 50 partitions comfortably covers hundreds of simultaneous live auctions;
# repartition upward as concurrent-auction volume grows (see architecture
# doc Section 10 capacity planning notes - this requires a new topic and a
# migration window, Kafka partitions cannot be safely reduced or reordered
# in place).
create_topic "auction.bids" 50 "${REPLICATION}" 604800000        # 7 day retention

# Final accept/reject decisions, also keyed by auction_id.
create_topic "auction.bid_results" 50 "${REPLICATION}" 604800000

# Downstream integration topics - each consumer group reads independently.
create_topic "auction.notifications" 12 "${REPLICATION}" 259200000   # 3 day retention
create_topic "auction.erp_sync" 12 "${REPLICATION}" 2592000000        # 30 day retention, financial data
create_topic "auction.fraud_signals" 12 "${REPLICATION}" 604800000

echo "Kafka topic initialization complete."
