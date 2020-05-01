use base64;
extern crate json;
use json::{Null, JsonValue};
use prost_types::{Timestamp};

use super::grpc::{event, Event, Timezone};

trait ToJson {
  fn to_json(&self) -> JsonValue;
}

impl ToJson for Timestamp {
  fn to_json(&self) -> JsonValue {
    json::array![self.seconds, self.nanos]
  }
}

impl<T: ToJson> ToJson for Option<T> {
  fn to_json(&self) -> JsonValue {
    match &self {
      Some(value) => value.to_json(),
      None => Null,
    }
  }
}

impl From<Timezone> for JsonValue {
  fn from(value: Timezone) -> JsonValue {
    json::object!{
      name: value.name.clone(),
      offset: value.offset,
    }
  }
}

impl From<&Event> for JsonValue {
  fn from(value: &Event) -> JsonValue {
    let account = base64::encode(&value.account);
    let uuid = base64::encode(&value.uuid);
    json::object!{
      uuid: uuid,
      account: account,
      application: value.application.clone(),
      type: value.r#type.clone(),
      name: value.name.clone(),
      description: value.description.clone(),
      timestamp: value.timestamp.to_json(),
      timezone: JsonValue::from(value.timezone.clone()),
      real_time: value.real_time,
      synced: value.synced.to_json(),
      additional: match &value.additional {
        None => Null,
        Some(event::Additional::AdditionalBytes(bytes)) => json::object!{
          bytes: base64::encode(bytes),
        },
        Some(event::Additional::AdditionalStr(string)) => json::object!{
          str: string.clone(),
        },
        Some(event::Additional::AdditionalYaml(string)) => json::object!{
          yaml: string.clone(),
        },
      },
    }
  }
}
