#![allow(unused_imports)]

use std::sync::RwLock;
use std::collections::HashMap;
use std::time::SystemTime;
use async_trait::async_trait;
use prost_types::Timestamp;

use super::grpc::{Event, Timezone, ErrorDetails};
use super::{Bytes, EventStorage};

type EventStream = Vec<Event>;
type ApplicationMap = HashMap<String, EventStream>;
type AccountMap = HashMap<Bytes, ApplicationMap>;

#[doc = "Store events in memory, partitioned by account and application."]
#[derive(Debug, Default)]
pub struct MemoryStorage {
    by_account: RwLock<AccountMap>,
}

#[async_trait]
impl EventStorage for MemoryStorage {
    async fn add(&self, event: Event) -> Result<Event, ErrorDetails> {
        let mut synced = event.clone();
        synced.synced = Some(Timestamp::from(SystemTime::now()));
        match self.by_account.write() {
            Ok(mut lock) => {
                &lock.entry(event.account).or_default()
                    .entry(event.application).or_default()
                    .push(synced.clone());
                Ok(synced)
            }
            Err(_) => Result::Err(ErrorDetails {
                code: 500,
                message: "Internal server error".to_string(),
            })
        }
    }
}
