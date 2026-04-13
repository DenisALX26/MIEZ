import { Component, type ErrorInfo, type ReactNode } from "react";
import { useLocation } from "react-router-dom";

interface BoundaryProps {
  children: ReactNode;
  resetKey: string;
}

interface BoundaryState {
  hasError: boolean;
}

class RouteErrorBoundaryClass extends Component<BoundaryProps, BoundaryState> {
  constructor(props: BoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): BoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Route render error:", error, info);
  }

  componentDidUpdate(prevProps: BoundaryProps): void {
    if (prevProps.resetKey !== this.props.resetKey && this.state.hasError) {
      this.setState({ hasError: false });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <section className="bg-white border border-red-200 rounded-lg p-6 text-red-700">
          <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
          <p className="text-sm">Please try another page or refresh the browser.</p>
        </section>
      );
    }

    return this.props.children;
  }
}

const RouteErrorBoundary = ({ children }: { children: ReactNode }) => {
  const location = useLocation();
  return <RouteErrorBoundaryClass resetKey={location.pathname} children={children} />;
};

export default RouteErrorBoundary;
