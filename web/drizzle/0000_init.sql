CREATE TYPE "public"."judge_run_status" AS ENUM('queued', 'running', 'done');--> statement-breakpoint
CREATE TYPE "public"."verdict" AS ENUM('accepted', 'wrong_answer', 'compile_error', 'runtime_error', 'time_limit_exceeded', 'memory_limit_exceeded', 'invalid_query', 'query_limit_exceeded', 'query_mismatch', 'oracle_timeout', 'invalid_witness', 'failed');--> statement-breakpoint
CREATE TABLE "judge_runs" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "judge_runs_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"submission_id" bigint NOT NULL,
	"test_data_version" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"status" "judge_run_status" DEFAULT 'queued' NOT NULL,
	"current_case" integer,
	"total_cases" integer,
	"judge_attempts" integer DEFAULT 0 NOT NULL,
	"judge_worker_id" text,
	"judge_lease_expires_at" timestamp with time zone,
	"completed_at" timestamp with time zone,
	"verdict" "verdict",
	"verdict_meta" jsonb,
	"metric_max_output_size" integer,
	"metric_max_runtime_ms" integer
);
--> statement-breakpoint
CREATE TABLE "problems" (
	"slug" text PRIMARY KEY NOT NULL,
	"abbreviation" text NOT NULL,
	"name" text NOT NULL,
	"complexity" text NOT NULL,
	"statement" text NOT NULL,
	"examples" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"is_root" boolean DEFAULT false NOT NULL,
	"time_limit_ms" integer NOT NULL,
	"memory_limit_mb" integer NOT NULL,
	"size_limits" jsonb NOT NULL,
	"content_hash" text NOT NULL,
	"data_hash" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "submissions" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "submissions_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"user_id" uuid NOT NULL,
	"from_problem" text NOT NULL,
	"to_problem" text NOT NULL,
	"source" text NOT NULL,
	"code_nbytes" integer GENERATED ALWAYS AS (octet_length(source)) STORED,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "submissions_distinct_problems" CHECK ("submissions"."from_problem" <> "submissions"."to_problem")
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"github_id" text NOT NULL,
	"username" text NOT NULL,
	"avatar_url" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "users_github_id_unique" UNIQUE("github_id")
);
--> statement-breakpoint
ALTER TABLE "judge_runs" ADD CONSTRAINT "judge_runs_submission_id_submissions_id_fk" FOREIGN KEY ("submission_id") REFERENCES "public"."submissions"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "submissions" ADD CONSTRAINT "submissions_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "submissions" ADD CONSTRAINT "submissions_from_problem_problems_slug_fk" FOREIGN KEY ("from_problem") REFERENCES "public"."problems"("slug") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "submissions" ADD CONSTRAINT "submissions_to_problem_problems_slug_fk" FOREIGN KEY ("to_problem") REFERENCES "public"."problems"("slug") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "judge_runs_submission" ON "judge_runs" USING btree ("submission_id","created_at" DESC NULLS LAST);--> statement-breakpoint
CREATE INDEX "judge_runs_queue" ON "judge_runs" USING btree ("created_at") WHERE "judge_runs"."status" in ('queued', 'running');--> statement-breakpoint
CREATE UNIQUE INDEX "problems_unique_root" ON "problems" USING btree ("is_root") WHERE "problems"."is_root";--> statement-breakpoint
CREATE INDEX "submissions_user_edge" ON "submissions" USING btree ("user_id","from_problem","to_problem");--> statement-breakpoint
CREATE INDEX "submissions_edge" ON "submissions" USING btree ("from_problem","to_problem");--> statement-breakpoint
CREATE VIEW "public"."judge_run_results" AS (select "judge_runs"."id", "judge_runs"."submission_id", "judge_runs"."status", "judge_runs"."created_at", "judge_runs"."verdict", "judge_runs"."metric_max_output_size", "judge_runs"."metric_max_runtime_ms", "submissions"."code_nbytes" from "judge_runs" inner join "submissions" on "submissions"."id" = "judge_runs"."submission_id");