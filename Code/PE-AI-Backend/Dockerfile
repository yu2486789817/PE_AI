FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn -DskipTests package

FROM eclipse-temurin:21-jre

WORKDIR /app
COPY --from=build /app/target/pe-ai-backend-1.0.0.jar app.jar

ENV SPRING_PROFILES_ACTIVE=prod
EXPOSE 5001

CMD ["java", "-jar", "app.jar"]
