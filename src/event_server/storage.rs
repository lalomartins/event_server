use async_trait::async_trait;
use tokio::sync::mpsc;

use super::grpc::{Event, EventsFilter, ErrorDetails};

pub type SimpleEventsStream = mpsc::Receiver<Result<Event, ErrorDetails>>;

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

    fn get(&self, filter: EventsFilter) -> SimpleEventsStream {
        println!("Get events from unimplemented storage: {:?}", filter);
        let (mut tx, rx) = mpsc::channel(1);
        tokio::spawn(async move {
            tx.send(Result::Err(ErrorDetails {
                        code: 501,
                        message: "Not Implemented".to_string(),
                    },
                )).await.unwrap();
            });
        rx
    }
}
