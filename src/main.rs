use std::env;
use std::sync::Arc;
use tonic::transport::Server;
mod event_server;
use event_server::memory_storage::MemoryStorage;
use event_server::file_storage::FileStorage;
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "0.0.0.0:50051".parse()?;
    let args: Vec<String> = env::args().collect();
    // XX there's probably a better way to do this…
    match args.get(1) {
        None => {
            let storage = Arc::new(MemoryStorage::default());
            let server = event_server::grpc::Server {storage: Arc::clone(&storage)};

            println!("Server listening on {}", addr);
            Server::builder()
                .add_service(event_server::grpc::event_server_server::EventServerServer::new(server))
                .serve_with_shutdown(addr, async {signal::ctrl_c().await.expect("failed to listen to interrupt signal");})
                .await?;
        
            println!("Interrupted. Dumping storage for debugging:\n{:?}", *storage);
            Ok(())
        }
        Some(root_path) => {
            let storage = Arc::new(FileStorage::new(root_path));
            let server = event_server::grpc::Server {storage: Arc::clone(&storage)};

            println!("Server listening on {}", addr);
            Server::builder()
                .add_service(event_server::grpc::event_server_server::EventServerServer::new(server))
                .serve_with_shutdown(addr, async {signal::ctrl_c().await.expect("failed to listen to interrupt signal");})
                .await?;
        
            println!("Interrupted.");
            Ok(())
        }
    }
}
