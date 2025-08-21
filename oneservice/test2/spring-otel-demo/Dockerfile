# syntax=docker/dockerfile:1

# Build stage
FROM maven:3.9.7-eclipse-temurin-17 AS build
WORKDIR /workspace
COPY pom.xml .
RUN --mount=type=cache,target=/root/.m2 mvn -q -e -DskipTests dependency:go-offline
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -q -DskipTests package

# Runtime image
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /workspace/target/spring-otel-demo-0.0.1-SNAPSHOT.jar /app/app.jar
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318 \
    JAVA_TOOL_OPTIONS="-Djava.security.egd=file:/dev/./urandom"
EXPOSE 8088
ENTRYPOINT ["java","-jar","/app/app.jar"]
