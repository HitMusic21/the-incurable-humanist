type Props = {
  className?: string;
  children: React.ReactNode;
};

export default function Card({ className = "", children }: Props) {
  return (
    <div className={`bg-surface rounded-xl shadow-soft border border-line ${className}`}>
      {children}
    </div>
  );
}
