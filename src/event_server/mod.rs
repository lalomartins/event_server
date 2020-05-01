pub mod grpc;
pub mod conversion;
pub mod storage;
pub mod memory_storage;
pub mod file_storage;
pub use storage::EventStorage;

pub type Bytes = std::vec::Vec<u8>;
