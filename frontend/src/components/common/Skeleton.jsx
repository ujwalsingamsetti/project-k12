/**
 * Skeleton – reusable shimmer placeholder.
 * Usage:
 *   <Skeleton className="h-4 w-32" />
 *   <Skeleton className="h-24 w-full rounded-xl" />
 */
export default function Skeleton({ className = '', ...props }) {
    return (
        <div
            className={`skeleton ${className}`}
            role="status"
            aria-label="Loading..."
            {...props}
        />
    );
}

/** Convenience: card-shaped skeleton */
export function SkeletonCard({ lines = 3 }) {
    return (
        <div className="card p-5 space-y-3">
            <Skeleton className="h-4 w-2/3" />
            {Array.from({ length: lines - 1 }, (_, i) => (
                <Skeleton key={i} className="h-3 w-full" />
            ))}
        </div>
    );
}

/** Convenience: table row skeleton */
export function SkeletonRow({ cols = 4 }) {
    return (
        <tr>
            {Array.from({ length: cols }, (_, i) => (
                <td key={i} className="px-4 py-3">
                    <Skeleton className="h-3 w-full" />
                </td>
            ))}
        </tr>
    );
}
