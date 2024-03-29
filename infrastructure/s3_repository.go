package infrastructure

import (
	"context"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/feature/s3/manager"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/nekochans/lgtm-cat-api/derrors"
	"github.com/nekochans/lgtm-cat-api/domain"
)

type s3Repository struct {
	uploader *manager.Uploader
	s3Bucket string
}

func NewS3Repository(u *manager.Uploader, s string) *s3Repository {
	return &s3Repository{uploader: u, s3Bucket: s}
}

func decideS3ContentType(ext string) string {
	contentType := ""

	switch ext {
	case ".png":
		contentType = "image/png"
	default:
		contentType = "image/jpeg"
	}

	return contentType
}
func (r *s3Repository) Upload(c context.Context, param *domain.UploadS3param) (err error) {
	defer derrors.Wrap(&err, "s3Repository.Upload(%+v)", param)

	const s3timeoutSecond = 10
	ctx, cancel := context.WithTimeout(c, s3timeoutSecond*time.Second)
	defer cancel()

	input := &s3.PutObjectInput{
		Bucket:      aws.String(r.s3Bucket),
		Body:        param.Body,
		ContentType: aws.String(decideS3ContentType(param.ImageExtension)),
		Key:         aws.String(param.Key),
	}

	_, err = r.uploader.Upload(ctx, input)
	if err != nil {
		ReportError(ctx, err)
		return err
	}

	return nil
}
