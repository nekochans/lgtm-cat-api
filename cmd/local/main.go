package main

import (
	"log"
	"net/http"

	"github.com/aws/aws-sdk-go-v2/feature/s3/manager"
	_ "github.com/go-sql-driver/mysql"
	db "github.com/nekochans/lgtm-cat-api/db/sqlc"
	"github.com/nekochans/lgtm-cat-api/handler"
	"github.com/nekochans/lgtm-cat-api/infrastructure"
)

var uploader *manager.Uploader
var queries *db.Queries

func main() {
	queries = infrastructure.NewSqlcQueries()
	uploader = infrastructure.NewUploader()

	r := handler.NewRouter(uploader, queries)
	err := http.ListenAndServe(":3333", r)
	if err != nil {
		log.Println(err)
		return
	}
}
