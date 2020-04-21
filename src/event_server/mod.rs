pub mod grpc;
pub mod storage;
pub mod memory_storage;
pub use storage::EventStorage;

pub type Bytes = std::vec::Vec<u8>;
