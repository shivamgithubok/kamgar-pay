import { PersonAvatar } from "@/components/person-avatar";
import { StatusPill } from "@/components/status-pill";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type DataCardProps = {
  title: string;
  description: string;
  columns: string[];
  rows: Array<Record<string, string | number>>;
  emptyMessage?: string;
};

export function DataCard({ title, description, columns, rows, emptyMessage = "No records available yet." }: DataCardProps) {
  return (
    <Card className="animate-fade-up overflow-hidden">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="p-0 pb-2">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column}>{column}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length > 0 ? (
              rows.map((row, index) => (
                <TableRow key={`${title}-${index}`}>
                  {columns.map((column) => {
                    const key = column.toLowerCase().replaceAll(" ", "");
                    const value = row[key] ?? row[column] ?? "";
                    const isStatus = column.toLowerCase() === "status";
                    const isName = column.toLowerCase() === "name" || column.toLowerCase() === "worker";
                    return (
                      <TableCell key={column}>
                        {isStatus ? (
                          <StatusPill value={String(value)} />
                        ) : isName ? (
                          <div className="flex items-center gap-3">
                            <PersonAvatar name={String(value)} />
                            <span className="font-medium">{value}</span>
                          </div>
                        ) : (
                          value
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell className="h-24 text-center text-muted-foreground" colSpan={columns.length}>
                  {emptyMessage}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
