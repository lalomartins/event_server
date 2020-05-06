#![allow(unused_imports)]

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use async_trait::async_trait;
use base64;
use chrono::{DateTime, Utc, Datelike};
extern crate json;
use prost_types::Timestamp;
extern crate sanitize_filename;
use tokio::sync::mpsc;

use super::grpc::{ErrorDetails, Event, EventsFilter};
use super::storage::{EventStorage, SimpleEventsStream};
use super::{conversion, Bytes};

#[doc = "Store events in memory, partitioned by account and application."]
#[derive(Debug)]
pub struct FileStorage {
    root_path: PathBuf,
}

impl FileStorage {
    pub fn new(root_path: &String) -> FileStorage {
        FileStorage {
            root_path: Path::new(root_path).to_path_buf(),
        }
    }
}

const SANITIZE_OPTIONS: sanitize_filename::Options = sanitize_filename::Options {
    replacement: "-",
    truncate: true,
    windows: true,
};

macro_rules! send_one {
    ($tx:expr, $data:expr) => {
        tokio::spawn(async move { $tx.send($data).await });
    };
}

#[async_trait]
impl EventStorage for FileStorage {
    async fn add(&self, event: Event) -> Result<Event, ErrorDetails> {
        let account = base64::encode(&event.account);
        let application =
            sanitize_filename::sanitize_with_options(&event.application, SANITIZE_OPTIONS.clone());
        let timestamp = Utc::now();
        let path = self
            .root_path
            .join(Path::new(&account))
            .join(Path::new(&application))
            .join(Path::new(&timestamp.year().to_string()));
        if let Err(e) = fs::create_dir_all(&path) {
            println!("Error creating file storage partition: {:?}", e);
            return Result::Err(ErrorDetails {
                code: 500,
                message: "Internal server error".to_string(),
            });
        }
        let filename = timestamp.format("%m-%d.jsonl").to_string();
        let mut synced = event.clone();
        synced.synced = Some(conversion::chrono_to_gprc(&timestamp));
        // TODO in a production setting, should lock first
        match fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(path.join(Path::new(&filename)))
        {
            Ok(mut f) => match f.write_all((json::stringify(&synced) + "\n").as_bytes()) {
                Ok(_) => Ok(synced),
                Err(e) => {
                    println!("Error writing to file storage: {:?}", e);
                    Result::Err(ErrorDetails {
                        code: 500,
                        message: "Internal server error".to_string(),
                    })
                }
            },
            Err(e) => {
                println!("Error creating file storage file: {:?}", e);
                Result::Err(ErrorDetails {
                    code: 500,
                    message: "Internal server error".to_string(),
                })
            }
        }
    }

    fn get(&self, filter: EventsFilter) -> SimpleEventsStream {
        let (mut tx, rx) = mpsc::channel(1);
        let account = base64::encode(&filter.account);
        let application =
            sanitize_filename::sanitize_with_options(&filter.application, SANITIZE_OPTIONS.clone());
        let path = self
            .root_path
            .join(Path::new(&account))
            .join(Path::new(&application));
        if path.is_dir() {
            tokio::spawn(async move {
                match path.read_dir() {
                    Err(error) => {
                        println!("Error opening storage: {:?}", error);
                        tx.send(Result::Err(ErrorDetails {
                            code: 500,
                            message: "Internal server error".to_string(),
                        }))
                        .await
                        .unwrap();
                    }
                    Ok(res) => {
                        for entry in res {
                            if let Ok(entry) = entry {
                                println!("year subpartition: {:?}", entry.path());
                                match entry.path().read_dir() {
                                    Err(error) => {
                                        println!("Error opening storage: {:?}", error);
                                        tx.send(Result::Err(ErrorDetails {
                                            code: 500,
                                            message: "Internal server error".to_string(),
                                        }))
                                        .await
                                        .unwrap();
                                    }
                                    Ok(res) => {
                                        for entry in res {
                                            if let Ok(entry) = entry {
                                                println!("day subpartition:  {:?}", entry.path());
                                                match fs::OpenOptions::new()
                                                    .read(true)
                                                    .open(entry.path())
                                                {
                                                    Ok(mut f) => {
                                                        // match f
                                                        //     .write_all((json::stringify(&synced) + "\n").as_bytes())
                                                        // {
                                                        //     Ok(_) => Ok(synced),
                                                        //     Err(e) => {
                                                        //         println!("Error writing to file storage: {:?}", e);
                                                        //         Result::Err(ErrorDetails {
                                                        //             code: 500,
                                                        //             message: "Internal server error".to_string(),
                                                        //         })
                                                        //     }
                                                        // }
                                                    }
                                                    Err(e) => {
                                                        println!("Error opening file storage file: {:?}", e);
                                                        tx.send(Result::Err(ErrorDetails {
                                                            code: 500,
                                                            message: "Internal server error".to_string(),
                                                        })).await.unwrap();
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            });
        // if let Err(e) = fs::create_dir_all(&path) {
        //     println!("Error creating file storage partition: {:?}", e);
        //     return Result::Err(ErrorDetails {
        //         code: 500,
        //         message: "Internal server error".to_string(),
        //     });
        // }
        // match self.by_account.read() {
        //     Ok(lock) => match lock.get(&filter.account) {
        //         None => {
        //             send_one!(
        //                 tx,
        //                 Result::Err(ErrorDetails {
        //                     code: 404,
        //                     message: "Account not found".to_string(),
        //                 })
        //             );
        //         }
        //         Some(partition) => match partition.get(&filter.application) {
        //             None => {
        //                 send_one!(
        //                     tx,
        //                     Result::Err(ErrorDetails {
        //                         code: 404,
        //                         message: "Application not found".to_string(),
        //                     })
        //                 );
        //             }
        //             Some(partition) => {
        //                 let copy = partition.clone();
        //                 tokio::spawn(async move {
        //                     for event in copy {
        //                         let mut matches = true;
        //                         if !filter.r#type.is_empty() {
        //                             matches = matches && event.r#type == filter.r#type;
        //                         }
        //                         if !filter.name.is_empty() {
        //                             matches = matches && event.name == filter.name;
        //                         }
        //                         if let Some(since) = &filter.since {
        //                             if let Some(synced) = &event.synced {
        //                                 matches = matches
        //                                     && ((synced.seconds > since.seconds)
        //                                         || (synced.seconds == since.seconds
        //                                             && synced.nanos > since.nanos));
        //                             }
        //                         }
        //                         if matches {
        //                             tx.send(Result::Ok(event.clone())).await.unwrap();
        //                         }
        //                     }
        //                 });
        //             }
        //         },
        //     },
        //     Err(error) => {
        //         println!("Error opening storage: {:?}", error);
        //         send_one!(
        //             tx,
        //             Result::Err(ErrorDetails {
        //                 code: 500,
        //                 message: "Internal server error".to_string(),
        //             })
        //         );
        //     }
        // }
        // send_one!(tx, Result::Err(ErrorDetails {
        //     code: 501,
        //     message: "Not Implemented".to_string(),
        // }));
        } else {
            send_one!(
                tx,
                Result::Err(ErrorDetails {
                    code: 404,
                    message: "No data found (account, application, or credentials are invalid)"
                        .to_string(),
                })
            );
        }
        rx
    }
}
