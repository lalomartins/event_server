use async_trait::async_trait;
use prost_types::Timestamp;
use std::collections::HashMap;
use std::sync::RwLock;
use std::time::SystemTime;
use tokio::sync::mpsc;

use super::grpc::{ErrorDetails, Event, EventsFilter, server_error};
use super::storage::{EventStorage, SimpleEventsStream};
use super::Bytes;

type EventStream = Vec<Event>;
type ApplicationMap = HashMap<String, EventStream>;
type AccountMap = HashMap<Bytes, ApplicationMap>;

#[doc = "Store events in memory, partitioned by account and application."]
#[derive(Debug, Default)]
pub struct MemoryStorage {
    by_account: RwLock<AccountMap>,
}

macro_rules! send_one {
    ($tx:expr, $data:expr) => {
        tokio::spawn(async move { $tx.send($data).await });
    };
}

#[async_trait]
impl EventStorage for MemoryStorage {
    async fn add(&self, event: Event) -> Result<Event, ErrorDetails> {
        let mut synced = event.clone();
        synced.synced = Some(Timestamp::from(SystemTime::now()));
        match self.by_account.write() {
            Ok(mut lock) => {
                &lock
                    .entry(event.account)
                    .or_default()
                    .entry(event.application)
                    .or_default()
                    .push(synced.clone());
                Ok(synced)
            }
            Err(_) => Result::Err(server_error()),
        }
    }

    fn get(&self, filter: EventsFilter) -> SimpleEventsStream {
        let (mut tx, rx) = mpsc::channel(1);
        match self.by_account.read() {
            Ok(lock) => match lock.get(&filter.account) {
                None => {
                    send_one!(
                        tx,
                        Result::Err(ErrorDetails {
                            code: 404,
                            message: "Account not found".to_string(),
                        })
                    );
                }
                Some(partition) => match partition.get(&filter.application) {
                    None => {
                        send_one!(
                            tx,
                            Result::Err(ErrorDetails {
                                code: 404,
                                message: "Application not found".to_string(),
                            })
                        );
                    }
                    Some(partition) => {
                        let copy = partition.clone();
                        tokio::spawn(async move {
                            for event in copy {
                                let mut matches = true;
                                if !filter.r#type.is_empty() {
                                    matches = matches && event.r#type == filter.r#type;
                                }
                                if !filter.name.is_empty() {
                                    matches = matches && event.name == filter.name;
                                }
                                if let Some(since) = &filter.since {
                                    if let Some(synced) = &event.synced {
                                        matches = matches
                                            && ((synced.seconds > since.seconds)
                                                || (synced.seconds == since.seconds
                                                    && synced.nanos > since.nanos));
                                    }
                                }
                                if matches {
                                    tx.send(Result::Ok(event.clone())).await.unwrap();
                                }
                            }
                        });
                    }
                },
            },
            Err(error) => {
                println!("Error opening storage: {:?}", error);
                send_one!(
                    tx,
                    Result::Err(server_error())
                );
            }
        }
        rx
    }
}
