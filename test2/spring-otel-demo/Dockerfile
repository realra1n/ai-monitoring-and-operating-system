# syntax=docker/dockerfile:1
FROM eclipse-temurin:17-jre as runtime

WORKDIR /app
# Copy jar built by Maven (we will bind mount or build in multi-stage later if needed)
ARG JAR_FILE=target/spring-otel-demo-0.0.1-SNAPSHOT.jar
COPY ${JAR_FILE} app.jar

# Default OTLP endpoint can be overridden by env
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318 \
    JAVA_TOOL_OPTIONS="-Djava.security.egd=file:/dev/./urandom"

EXPOSE 8088
ENTRYPOINT ["java","-jar","/app/app.jar"]
