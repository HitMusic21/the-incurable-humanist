import { Link } from "react-router-dom";

type Props =
  | ({ as: "link"; to: string } & React.ButtonHTMLAttributes<HTMLAnchorElement>)
  | ({ as?: "button"; to?: never } & React.ButtonHTMLAttributes<HTMLButtonElement>);

export default function PillButton(props: Props) {
  const base =
    "inline-flex items-center gap-2 px-6 h-12 rounded-pill bg-accent2 text-white shadow-soft hover:brightness-105 active:brightness-95 transition";
  if ("as" in props && props.as === "link" && props.to) {
    const { as, to, className = "", ...rest } = props;
    return (
      <Link to={to} className={`${base} ${className}`} {...rest}>
        {props.children}
      </Link>
    );
  }
  const { as, to, className = "", ...rest } = props as any;
  return (
    <button className={`${base} ${className}`} {...rest}>
      {props.children}
    </button>
  );
}
