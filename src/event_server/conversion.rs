use std::convert::TryFrom;

use base64;
use chrono::{DateTime, Utc};
extern crate json;
use json::{JsonValue, Null};
use prost_types::Timestamp;

use super::grpc::{event, Event, Timezone, ErrorDetails, server_error};

trait JsonConvert {
    fn to_json(&self) -> JsonValue;
    fn from_json(value: &JsonValue) -> Self;
}

impl JsonConvert for Timestamp {
    fn to_json(&self) -> JsonValue {
        json::array![self.seconds, self.nanos]
    }

    fn from_json(value: &JsonValue) -> Self {
        if !value.is_array() {
            panic!()
        }
        Timestamp {seconds: value[0].as_i64().unwrap_or_default(), nanos: value[1].as_i32().unwrap_or_default()}
    }
}

impl JsonConvert for Timezone {
    fn to_json(&self) -> JsonValue {
        json::object! {
            name: self.name.clone(),
            offset: self.offset,
        }
    }

    fn from_json(value: &JsonValue) -> Self {
        if !value.is_object() {
            panic!()
        }
        Timezone {name: value[0].to_string(), offset: value[1].as_i32().unwrap_or_default()}
    }
}

impl JsonConvert for event::Additional {
    fn to_json(&self) -> JsonValue {
        match self {
            event::Additional::AdditionalBytes(bytes) => json::object!{
                bytes: base64::encode(bytes),
            },
            event::Additional::AdditionalStr(string) => json::object!{
                str: string.clone(),
            },
            event::Additional::AdditionalYaml(string) => json::object!{
                yaml: string.clone(),
            },
        }
    }

    fn from_json(value: &JsonValue) -> Self {
        if let JsonValue::Object(value) = value {
            if let Some(bytes) = value.get("bytes") {
                event::Additional::AdditionalBytes(base64::decode(bytes.to_string()).unwrap())
            } else if let Some(str) = value.get("str") {
                event::Additional::AdditionalStr(str.to_string())
            } else if let Some(yaml) = value.get("yaml") {
                event::Additional::AdditionalYaml(yaml.to_string())
            } else {
                event::Additional::AdditionalYaml(String::default())
            }
        } else {
            event::Additional::AdditionalYaml(String::default())
        }
    }
}

impl<T: JsonConvert> JsonConvert for Option<T> {
    fn to_json(&self) -> JsonValue {
        match &self {
            Some(value) => value.to_json(),
            None => Null,
        }
    }

    fn from_json(value: &JsonValue) -> Option<T> {
        if value.is_null() {
            None
        } else {
            Some(T::from_json(&value))
        }
    }
}

impl From<&Event> for JsonValue {
    fn from(value: &Event) -> JsonValue {
        let account = base64::encode(&value.account);
        let uuid = base64::encode(&value.uuid);
        json::object! {
            uuid: uuid,
            account: account,
            application: value.application.clone(),
            type: value.r#type.clone(),
            name: value.name.clone(),
            description: value.description.clone(),
            timestamp: value.timestamp.to_json(),
            timezone: value.timezone.to_json(),
            real_time: value.real_time,
            synced: value.synced.to_json(),
            additional: value.additional.to_json(),
        }
    }
}

fn event_from_json(value: &JsonValue) -> Result<Event, json::Error> {
    let account = base64::decode(&value["account"].to_string()).unwrap_or(vec![]);
    let uuid = base64::decode(&value["uuid"].to_string()).unwrap_or(vec![]);
    Ok(Event {
        uuid: uuid,
        account: account,
        application: value["application"].to_string(),
        r#type: value["type"].to_string(),
        name: value["name"].to_string(),
        description: value["description"].to_string(),
        timestamp: Option::<Timestamp>::from_json(&value["timestamp"]),
        timezone: Option::<Timezone>::from_json(&value["timezone"]),
        real_time: value["real_time"].as_bool().unwrap_or_default(),
        synced: Option::<Timestamp>::from_json(&value["synced"]),
        additional: Option::<event::Additional>::from_json(&value["additional"]),
    })
}

impl TryFrom<&JsonValue> for Event {
    type Error = ErrorDetails;

    fn try_from(value: &JsonValue) -> Result<Self, Self::Error> {
        event_from_json(value).or(Err(server_error()))
    }
}

pub fn chrono_to_gprc(timestamp: &DateTime<Utc>) -> Timestamp {
    let nanos = timestamp.timestamp_nanos();
    Timestamp {seconds: nanos / 1000000000, nanos: (nanos % 1000000) as i32}
}
