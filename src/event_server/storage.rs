#![allow(unused_imports)]

use async_trait::async_trait;

use super::grpc::{Event, Timezone, ErrorDetails};

#[doc = "Trait for a method of storing events (persistent or not)."]
#[async_trait]
pub trait EventStorage: Send + Sync + 'static {
    async fn add(&self, event: Event) -> Result<Event, ErrorDetails> {
        println!("Add event to unimplemented storage: {:?}", event);
        Result::Err(ErrorDetails {
            code: 501,
            message: "Not Implemented".to_string(),
        })
    }
}
