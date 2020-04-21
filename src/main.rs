use std::sync::Arc;
use tonic::transport::Server;
mod event_server;
use event_server::memory_storage::MemoryStorage;
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let storage = Arc::new(MemoryStorage::default());
    let server = event_server::grpc::Server::<MemoryStorage> {storage: Arc::clone(&storage)};

    Server::builder()
        .add_service(event_server::grpc::event_server_server::EventServerServer::new(server))
        .serve_with_shutdown(addr, async {signal::ctrl_c().await.expect("failed to listen to interrupt signal");})
        .await?;

    println!("Interrupted. Dumping storage for debugging:\n{:?}", *storage);
    Ok(())
}
