import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";

type DiffViewProps = {
  left: string;
  right: string;
};

export function DiffView({ left, right }: DiffViewProps) {
  return (
    <div className="not-prose">
      <ReactDiffViewer
        oldValue={left}
        newValue={right}
        splitView={true}
        compareMethod={DiffMethod.LINES}
        leftTitle="Current"
        rightTitle="Proposed"
        showDiffOnly={false}
      />
    </div>
  );
}
