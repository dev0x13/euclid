FROM openjdk:8-jdk

WORKDIR /

ARG jar_file 

COPY ${jar_file} app.jar

EXPOSE 8080

ENTRYPOINT java -jar ./app.jar
