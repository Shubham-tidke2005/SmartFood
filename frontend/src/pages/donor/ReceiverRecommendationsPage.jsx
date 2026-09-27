import {
  BrainCircuit,
  CheckCircle2,
  Clock3,
  MapPin,
  RefreshCw,
  Sparkles,
  Users,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import api from "../../lib/api";


function getErrorMessage(error) {
  const responseData = error?.response?.data;

  if (typeof responseData?.detail === "string") {
    return responseData.detail;
  }

  return (
    "Something went wrong while loading "
    + "receiver recommendations."
  );
}


function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}


function scoreColor(score) {
  if (Number(score) >= 80) {
    return "text-emerald-600";
  }

  if (Number(score) >= 60) {
    return "text-blue-600";
  }

  return "text-amber-600";
}


function RecommendationSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((item) => (
        <div
          key={item}
          className={
            "animate-pulse rounded-2xl border "
            + "border-slate-200 bg-white p-6"
          }
        >
          <div className="h-5 w-48 rounded bg-slate-200" />
          <div className="mt-3 h-4 w-32 rounded bg-slate-100" />
          <div className="mt-6 h-20 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}


function RecommendationCard({
  candidate,
}) {
  return (
    <article
      className={
        "rounded-2xl border border-slate-200/80 "
        + "bg-white p-5 shadow-sm transition-all "
        + "duration-200 hover:-translate-y-1 "
        + "hover:shadow-xl hover:shadow-blue-500/5 "
        + "dark:border-slate-700/60 "
        + "dark:bg-slate-800"
      }
    >
      <div
        className={
          "flex flex-col gap-4 sm:flex-row "
          + "sm:items-start sm:justify-between"
        }
      >
        <div className="flex items-start gap-4">
          <div
            className={
              "flex h-12 w-12 shrink-0 items-center "
              + "justify-center rounded-2xl bg-blue-50 "
              + "font-bold text-blue-700 "
              + "dark:bg-blue-500/10 dark:text-blue-300"
            }
          >
            #{candidate.rank}
          </div>

          <div>
            <h2
              className={
                "text-lg font-semibold text-slate-900 "
                + "dark:text-white"
              }
            >
              {candidate.organization_name}
            </h2>

            <p
              className={
                "mt-1 text-sm text-slate-500 "
                + "dark:text-slate-400"
              }
            >
              {candidate.receiver_name}
            </p>
          </div>
        </div>

        <div className="sm:text-right">
          <p
            className={
              "text-3xl font-bold "
              + scoreColor(candidate.score)
            }
          >
            {candidate.score}
          </p>

          <p
            className={
              "text-xs font-medium uppercase "
              + "tracking-wide text-slate-500"
            }
          >
            suitability score
          </p>
        </div>
      </div>

      <div
        className={
          "mt-5 grid gap-3 sm:grid-cols-2"
        }
      >
        <div
          className={
            "flex items-center gap-3 rounded-xl "
            + "bg-slate-50 p-3 dark:bg-slate-900/50"
          }
        >
          <MapPin
            className="h-5 w-5 text-sky-500"
            aria-hidden="true"
          />

          <div>
            <p className="text-xs text-slate-500">
              Approximate distance
            </p>

            <p
              className={
                "font-medium text-slate-900 "
                + "dark:text-white"
              }
            >
              {candidate.approximate_distance_km
                ? `${candidate.approximate_distance_km} km`
                : "Not available"}
            </p>
          </div>
        </div>

        <div
          className={
            "flex items-center gap-3 rounded-xl "
            + "bg-slate-50 p-3 dark:bg-slate-900/50"
          }
        >
          <Users
            className="h-5 w-5 text-blue-500"
            aria-hidden="true"
          />

          <div>
            <p className="text-xs text-slate-500">
              Remaining capacity
            </p>

            <p
              className={
                "font-medium text-slate-900 "
                + "dark:text-white"
              }
            >
              {candidate.remaining_capacity}{" "}
              {candidate.feature_snapshot?.unit}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-5">
        <h3
          className={
            "flex items-center gap-2 text-sm "
            + "font-semibold text-slate-900 "
            + "dark:text-white"
          }
        >
          <Sparkles
            className="h-4 w-4 text-blue-600"
            aria-hidden="true"
          />
          Why this receiver is recommended
        </h3>

        <ul className="mt-3 space-y-2">
          {(candidate.explanations || []).map(
            (explanation) => (
              <li
                key={explanation}
                className={
                  "flex items-start gap-2 text-sm "
                  + "text-slate-600 dark:text-slate-300"
                }
              >
                <CheckCircle2
                  className={
                    "mt-0.5 h-4 w-4 shrink-0 "
                    + "text-emerald-500"
                  }
                  aria-hidden="true"
                />

                <span>{explanation}</span>
              </li>
            ),
          )}
        </ul>
      </div>

      <div
        className={
          "mt-5 rounded-xl border border-amber-200 "
          + "bg-amber-50 p-3 text-xs text-amber-800 "
          + "dark:border-amber-500/30 "
          + "dark:bg-amber-500/10 "
          + "dark:text-amber-200"
        }
      >
        This recommendation does not allocate the donation.
        The receiver must submit a request and the donor must
        approve it.
      </div>
    </article>
  );
}


export default function ReceiverRecommendationsPage() {
  const { donationId } = useParams();

  const [recommendationRun, setRecommendationRun] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const endpoint =
    `/recommendations/donations/${donationId}/`;

  const loadRecommendations = useCallback(
    async () => {
      setLoading(true);
      setError("");

      try {
        const response = await api.get(endpoint);
        setRecommendationRun(response.data);
      } catch (requestError) {
        if (requestError?.response?.status === 404) {
          setRecommendationRun(null);
        } else {
          setError(
            getErrorMessage(requestError),
          );
        }
      } finally {
        setLoading(false);
      }
    },
    [endpoint],
  );

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  async function generateRecommendations() {
    setGenerating(true);
    setError("");

    try {
      const response = await api.post(
        endpoint,
        {},
      );

      setRecommendationRun(response.data);
    } catch (requestError) {
      setError(
        getErrorMessage(requestError),
      );
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-28 animate-pulse rounded-2xl bg-slate-200" />
        <RecommendationSkeleton />
      </div>
    );
  }

  return (
    <main className="space-y-6">
      <section
        className={
          "rounded-3xl bg-gradient-to-br "
          + "from-blue-600 to-sky-500 p-6 "
          + "text-white shadow-lg shadow-blue-500/10 "
          + "sm:p-8"
        }
      >
        <div
          className={
            "flex flex-col gap-5 sm:flex-row "
            + "sm:items-center sm:justify-between"
          }
        >
          <div>
            <div
              className={
                "mb-3 inline-flex items-center gap-2 "
                + "rounded-full bg-white/15 px-3 py-1 "
                + "text-sm backdrop-blur"
              }
            >
              <BrainCircuit className="h-4 w-4" />
              Explainable recommendation baseline
            </div>

            <h1 className="text-2xl font-bold sm:text-3xl">
              Recommended receivers
            </h1>

            <p className="mt-2 max-w-2xl text-blue-50">
              Eligible receivers are ranked using category,
              capacity, availability, approximate distance and
              successful donation history.
            </p>
          </div>

          <button
            type="button"
            onClick={generateRecommendations}
            disabled={generating}
            className={
              "inline-flex min-h-11 items-center "
              + "justify-center gap-2 rounded-xl "
              + "bg-white px-5 py-3 font-semibold "
              + "text-blue-700 shadow-sm transition "
              + "hover:bg-blue-50 active:scale-[0.98] "
              + "focus-visible:outline-none "
              + "focus-visible:ring-2 "
              + "focus-visible:ring-white "
              + "disabled:cursor-not-allowed "
              + "disabled:opacity-60"
            }
          >
            <RefreshCw
              className={
                `h-5 w-5 ${
                  generating ? "animate-spin" : ""
                }`
              }
            />

            {generating
              ? "Generating..."
              : recommendationRun
                ? "Refresh ranking"
                : "Generate ranking"}
          </button>
        </div>
      </section>

      {error && (
        <div
          role="alert"
          className={
            "rounded-2xl border border-red-200 "
            + "bg-red-50 p-4 text-sm text-red-700 "
            + "dark:border-red-500/30 "
            + "dark:bg-red-500/10 dark:text-red-200"
          }
        >
          {error}
        </div>
      )}

      {!recommendationRun && !error && (
        <section
          className={
            "rounded-2xl border border-dashed "
            + "border-slate-300 bg-white p-10 "
            + "text-center dark:border-slate-700 "
            + "dark:bg-slate-800"
          }
        >
          <BrainCircuit
            className={
              "mx-auto h-12 w-12 text-slate-400"
            }
          />

          <h2
            className={
              "mt-4 text-lg font-semibold "
              + "text-slate-900 dark:text-white"
            }
          >
            No recommendation run yet
          </h2>

          <p
            className={
              "mx-auto mt-2 max-w-md text-sm "
              + "text-slate-500 dark:text-slate-400"
            }
          >
            Generate a ranking to find verified and currently
            eligible receivers for this donation.
          </p>
        </section>
      )}

      {recommendationRun && (
        <>
          <section
            className={
              "flex flex-col gap-3 rounded-2xl "
              + "border border-slate-200 bg-white p-4 "
              + "sm:flex-row sm:items-center "
              + "sm:justify-between dark:border-slate-700 "
              + "dark:bg-slate-800"
            }
          >
            <div>
              <p
                className={
                  "font-semibold text-slate-900 "
                  + "dark:text-white"
                }
              >
                {recommendationRun.candidate_count} eligible
                receiver(s)
              </p>

              <p className="text-sm text-slate-500">
                Model: {recommendationRun.model_version}
              </p>
            </div>

            <div
              className={
                "flex items-center gap-2 text-sm "
                + "text-slate-500"
              }
            >
              <Clock3 className="h-4 w-4" />
              {formatDateTime(
                recommendationRun.created_at,
              )}
            </div>
          </section>

          {recommendationRun.candidates.length === 0 ? (
            <section
              className={
                "rounded-2xl border border-dashed "
                + "border-slate-300 bg-white p-10 "
                + "text-center dark:border-slate-700 "
                + "dark:bg-slate-800"
              }
            >
              <Users
                className={
                  "mx-auto h-12 w-12 text-slate-400"
                }
              />

              <h2
                className={
                  "mt-4 font-semibold text-slate-900 "
                  + "dark:text-white"
                }
              >
                No eligible receivers found
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Check receiver preferences, requirements,
                capacity, availability and service-area data.
              </p>
            </section>
          ) : (
            <section className="grid gap-5 xl:grid-cols-2">
              {recommendationRun.candidates.map(
                (candidate) => (
                  <RecommendationCard
                    key={candidate.id}
                    candidate={candidate}
                  />
                ),
              )}
            </section>
          )}
        </>
      )}

      <Link
        to={`/donor/donations/${donationId}`}
        className={
          "inline-flex min-h-11 items-center "
          + "rounded-xl border border-slate-300 "
          + "px-4 py-2 text-sm font-medium "
          + "text-slate-700 transition hover:bg-slate-100 "
          + "focus-visible:outline-none "
          + "focus-visible:ring-2 "
          + "focus-visible:ring-blue-500 "
          + "dark:border-slate-700 "
          + "dark:text-slate-200 "
          + "dark:hover:bg-slate-800"
        }
      >
        Back to donation
      </Link>
    </main>
  );
}