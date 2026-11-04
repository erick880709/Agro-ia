output "queue_url" {
  value = aws_sqs_queue.this.url
}

output "consumer_policy_arn" {
  value = aws_iam_policy.consumer.arn
}
