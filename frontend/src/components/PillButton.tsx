import { Link } from "react-router-dom";

type Props =
  | ({ as: "link"; to: string } & React.ButtonHTMLAttributes<HTMLAnchorElement>)
  | ({ as?: "button"; to?: never } & React.ButtonHTMLAttributes<HTMLButtonElement>);

export default function PillButton(props: Props) {
  const base =
    "inline-flex items-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 transition";
  if ("as" in props && props.as === "link" && props.to) {
    // Destructure to strip `as`/`to` from the spread — they're not valid <a> attrs.
    const { as: _as, to, className = "", ...rest } = props;
    void _as;
    return (
      <Link to={to} className={`${base} ${className}`} {...rest}>
        {props.children}
      </Link>
    );
  }
  const { as: _as, to: _to, className = "", ...rest } = props as {
    as?: unknown;
    to?: unknown;
    className?: string;
  } & React.ButtonHTMLAttributes<HTMLButtonElement>;
  void _as;
  void _to;
  return (
    <button className={`${base} ${className}`} {...rest}>
      {props.children}
    </button>
  );
}
