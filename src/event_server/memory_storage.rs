#![allow(unused_imports, dead_code)]

use async_trait::async_trait;

use super::grpc::{Event, Timezone, ErrorDetails};
use super::{Bytes, EventStorage};

#[doc = "Store events in memory, partitioned by account and application."]
#[derive(Debug, Default)]
pub struct MemoryStorage {

}

#[async_trait]
impl EventStorage for MemoryStorage {
}
