use tonic::transport::Server;
mod event_server;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let server = event_server::grpc::Server::default();

    Server::builder()
        .add_service(event_server::grpc::event_server_server::EventServerServer::new(server))
        .serve(addr)
        .await?;

    Ok(())
}
