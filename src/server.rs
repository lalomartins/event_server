use tokio::sync::{mpsc, oneshot};
use tonic::{transport::Server, Request, Response, Status, Streaming};

pub mod event_server {
    tonic::include_proto!("eventserver"); // The string specified here must match the proto package name
}

use event_server::event_server_server::{EventServer, EventServerServer};
use event_server::{
    event_operation_result, event_stream_item, ErrorDetails, Event, EventOperationResult,
    EventStreamItem, GetEventsRequest, GetEventsResponse, PushEventsRequest, PushEventsResponse,
    Timezone, WatchEventsRequest, WatchEventsResponse,
};

#[derive(Debug, Default)]
pub struct MyServer {}

#[tonic::async_trait]
impl EventServer for MyServer {
    type PushEventsStream = mpsc::Receiver<Result<PushEventsResponse, Status>>;

    async fn push_events(
        &self,
        request: Request<Streaming<PushEventsRequest>>,
    ) -> Result<Response<Self::PushEventsStream>, Status> {
        let (mut tx, rx) = mpsc::channel(4);
        tokio::spawn(async move {
            tx.send(Ok(PushEventsResponse {
                result: Some(EventOperationResult {
                    item_content: Some(event_operation_result::ItemContent::Error(ErrorDetails {
                        code: 501,
                        message: "Not Implemented".to_string(),
                    })),
                }),
            }))
            .await
            .unwrap();
        });

        Ok(Response::new(rx))
    }

    type GetEventsStream = mpsc::Receiver<Result<GetEventsResponse, Status>>;

    async fn get_events(
        &self,
        request: Request<GetEventsRequest>,
    ) -> Result<Response<Self::GetEventsStream>, Status> {
        let (mut tx, rx) = mpsc::channel(4);
        tokio::spawn(async move {
            tx.send(Ok(GetEventsResponse {
                result: Some(EventOperationResult {
                    item_content: Some(event_operation_result::ItemContent::Error(ErrorDetails {
                        code: 501,
                        message: "Not Implemented".to_string(),
                    })),
                }),
            }))
            .await
            .unwrap();
        });

        Ok(Response::new(rx))
    }

    type WatchEventsStream = mpsc::Receiver<Result<WatchEventsResponse, Status>>;

    async fn watch_events(
        &self,
        request: Request<WatchEventsRequest>,
    ) -> Result<Response<Self::WatchEventsStream>, Status> {
        let (mut tx, rx) = mpsc::channel(4);
        tokio::spawn(async move {
            tx.send(Ok(WatchEventsResponse {
                item: Some(EventStreamItem {
                    item_content: Some(event_stream_item::ItemContent::Error(ErrorDetails {
                        code: 501,
                        message: "Not Implemented".to_string(),
                    })),
                }),
            }))
            .await
            .unwrap();
        });

        Ok(Response::new(rx))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let server = MyServer::default();

    Server::builder()
        .add_service(EventServerServer::new(server))
        .serve(addr)
        .await?;

    Ok(())
}
