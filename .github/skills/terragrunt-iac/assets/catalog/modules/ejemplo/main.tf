# Servicio de ejemplo: cola SQS cuyo consumidor tiene permiso de escritura sobre la tabla.
resource "aws_sqs_queue" "this" {
  name                       = var.name
  visibility_timeout_seconds = var.visibility_timeout
  sqs_managed_sse_enabled    = true
}

data "aws_iam_policy_document" "consumer" {
  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.this.arn]
  }

  statement {
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem"]
    resources = [var.table_arn]
  }
}

resource "aws_iam_policy" "consumer" {
  name   = "${var.name}-consumer"
  policy = data.aws_iam_policy_document.consumer.json
}
