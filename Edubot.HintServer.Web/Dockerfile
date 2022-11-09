#See https://aka.ms/containerfastmode to understand how Visual Studio uses this Dockerfile to build your images for faster debugging.

FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
WORKDIR /app
EXPOSE 80

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["Edubot.HintServer.Web/Edubot.HintServer.Web.csproj", "Edubot.HintServer.Web/"]
RUN dotnet restore "Edubot.HintServer.Web/Edubot.HintServer.Web.csproj"
COPY . .
WORKDIR "/src/Edubot.HintServer.Web"
RUN dotnet build "Edubot.HintServer.Web.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Edubot.HintServer.Web.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Edubot.HintServer.Web.dll"]