#![allow(unused_imports)]

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use async_trait::async_trait;
use base64;
use chrono::{DateTime, Utc};
extern crate json;
use prost_types::Timestamp;
extern crate sanitize_filename;

use super::grpc::{ErrorDetails, Event, Timezone};
use super::{Bytes, EventStorage, conversion};

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

const SANITIZE_OPTIONS: sanitize_filename::Options = sanitize_filename::Options{
    replacement: "-",
    truncate: true,
    windows: true,
};

#[async_trait]
impl EventStorage for FileStorage {
    async fn add(&self, event: Event) -> Result<Event, ErrorDetails> {
        let account = base64::encode(&event.account);
        let application = sanitize_filename::sanitize_with_options(&event.application, SANITIZE_OPTIONS.clone());
        let path = self
            .root_path
            .join(Path::new(&account))
            .join(Path::new(&application));
        if let Err(e) = fs::create_dir_all(&path) {
            println!("Error creating file storage partition: {:?}", e);
            return Result::Err(ErrorDetails {
                code: 500,
                message: "Internal server error".to_string(),
            });
        }
        let timestamp = Utc::now();
        let filename = timestamp.format("%Y-%m-%d.jsonl").to_string();
        let mut synced = event.clone();
        synced.synced = Some(Timestamp::from(SystemTime::from(timestamp)));
        // TODO in a production setting, should lock first
        match fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(path.join(Path::new(&filename)))
        {
            Ok(mut f) => {
                match f.write_all((json::stringify(&synced) + "\n").as_bytes()) {
                    Ok(_) => Ok(synced),
                    Err(e) => {
                        println!("Error writing to file storage: {:?}", e);
                        Result::Err(ErrorDetails {
                            code: 500,
                            message: "Internal server error".to_string(),
                        })
                    }
                }
            }
            Err(e) => {
                println!("Error creating file storage file: {:?}", e);
                Result::Err(ErrorDetails {
                    code: 500,
                    message: "Internal server error".to_string(),
                })
            }
        }
        // match self.by_account.write() {
        //     Ok(mut lock) => {
        //         &lock.entry(event.account).or_default()
        //             .entry(event.application).or_default()
        //             .push(synced.clone());
        //         Ok(synced)
        //     }
        //     Err(_) => Result::Err(ErrorDetails {
        //         code: 500,
        //         message: "Internal server error".to_string(),
        //     })
        // }
    }
}
