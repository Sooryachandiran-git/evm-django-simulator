FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o auditcc

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/auditcc .
EXPOSE 9999
CMD ["./auditcc"]
