tonic::include_proto!("eventserver"); // The string specified here must match the proto package name

use tokio::sync::mpsc;
use tonic::{Request, Response, Status, Streaming};

#[derive(Debug, Default)]
pub struct Server {}

#[tonic::async_trait]
impl event_server_server::EventServer for Server {
    type PushEventsStream = mpsc::Receiver<Result<PushEventsResponse, Status>>;

    async fn push_events(
        &self,
        _request: Request<Streaming<PushEventsRequest>>,
    ) -> Result<Response<Self::PushEventsStream>, Status> {
        let (mut tx, rx) = mpsc::channel(4);
        tokio::spawn(async move {
            tx.send(Ok(PushEventsResponse {
                result: Some(EventOperationResult {
                    item_content: Some(event_operation_result::ItemContent::Error(
                        ErrorDetails {
                            code: 501,
                            message: "Not Implemented".to_string(),
                        },
                    )),
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
        _request: Request<GetEventsRequest>,
    ) -> Result<Response<Self::GetEventsStream>, Status> {
        let (mut tx, rx) = mpsc::channel(4);
        tokio::spawn(async move {
            tx.send(Ok(GetEventsResponse {
                result: Some(EventOperationResult {
                    item_content: Some(event_operation_result::ItemContent::Error(
                        ErrorDetails {
                            code: 501,
                            message: "Not Implemented".to_string(),
                        },
                    )),
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
        _request: Request<WatchEventsRequest>,
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
