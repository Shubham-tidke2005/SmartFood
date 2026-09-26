import {
  Construction,
} from "lucide-react";

import { EmptyState } from "../components/ui/FeedbackStates";

export default function FeaturePlaceholderPage({
  title,
  description,
}) {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-black tracking-tight text-slate-950 dark:text-white">
          {title}
        </h1>

        <p className="mt-2 text-slate-500 dark:text-slate-400">
          {description}
        </p>
      </div>

      <EmptyState
        icon={Construction}
        title={`${title} is ready for implementation`}
        description="The protected route, responsive layout and role permissions are already configured."
      />
    </div>
  );
}