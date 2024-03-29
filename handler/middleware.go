package handler

import (
	"context"
	"fmt"
	"net/http"

	"github.com/getsentry/sentry-go"

	"github.com/nekochans/lgtm-cat-api/infrastructure"
)

type contextKey string

const logKey contextKey = "log"

func withLogger(logger infrastructure.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		fn := func(w http.ResponseWriter, r *http.Request) {
			requestId := r.Header.Get("X-Request-Id")
			withLogger := logger.With(infrastructure.Field{
				Key:   "x_request_id",
				Value: requestId,
			})

			ctx := context.WithValue(r.Context(), logKey, withLogger)
			next.ServeHTTP(w, r.WithContext(ctx))
		}
		return http.HandlerFunc(fn)
	}
}

func extractLogger(ctx context.Context) infrastructure.Logger {
	return ctx.Value(logKey).(infrastructure.Logger)
}

func recovery(next http.Handler) http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rvr := recover(); rvr != nil {
				if rvr == http.ErrAbortHandler {
					panic(rvr)
				}

				err, ok := rvr.(error)
				if !ok {
					err = fmt.Errorf("panic recover: %v", rvr)
				}

				logger := extractLogger(r.Context())
				logger.Error(err)

				RenderErrorResponse(w, InternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	}
	return http.HandlerFunc(fn)
}

func sentryRequestId(next http.Handler) http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		requestId := r.Header.Get("X-Request-Id")
		ctx := r.Context()

		if hub := sentry.GetHubFromContext(ctx); hub != nil {
			hub.Scope().SetTag("x_request_id", requestId)
		}

		r = r.WithContext(ctx)
		next.ServeHTTP(w, r)
	}
	return http.HandlerFunc(fn)
}
