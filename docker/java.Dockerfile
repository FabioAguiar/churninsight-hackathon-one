# ===== Stage 1: build =====
FROM maven:3.9.6-eclipse-temurin-17 AS build

WORKDIR /build

# Copia arquivos de build
COPY backend_java/pom.xml .
RUN mvn dependency:go-offline

# Copia código fonte
COPY backend_java/src ./src

# Build da aplicação
RUN mvn clean package -DskipTests


# ===== Stage 2: runtime =====
FROM eclipse-temurin:17-jre

WORKDIR /app

# Copia o jar gerado
COPY --from=build /build/target/*.jar app.jar

# Expõe porta padrão do Spring Boot
EXPOSE 8080

# Comando de inicialização
ENTRYPOINT ["java", "-jar", "app.jar"]
