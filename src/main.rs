use tonic::transport::Server;
mod event_server;
use event_server::memory_storage::MemoryStorage;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let server = event_server::grpc::Server::<MemoryStorage> {storage: MemoryStorage::default()};

    Server::builder()
        .add_service(event_server::grpc::event_server_server::EventServerServer::new(server))
        .serve(addr)
        .await?;

    Ok(())
}
